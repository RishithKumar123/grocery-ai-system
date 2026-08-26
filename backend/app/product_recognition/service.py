from typing import Optional, List, Dict, Any
from app.product_recognition import repository
from app.data.models.product_model import ProductModel
import math


class ProductRecognitionService:
    def __init__(self, db_session, config: Optional[dict] = None):
        self.db = db_session
        self.repo = repository.SQLAlchemyProductRecognitionRepository(self.db)
        # Default weights; higher weight for barcode
        default = {"barcode": 0.6, "ocr": 0.2, "embedding": 0.1, "yolo": 0.05, "metadata": 0.05}
        self.weights = {**default, **(config or {})}

    def _score_barcode(self, barcode_value: str) -> Optional[Dict[str, Any]]:
        prod = self.repo.find_by_barcode(barcode_value)
        if not prod:
            return None
        # perfect match
        return {"product": prod, "score": 1.0, "component": "barcode", "details": {"value": barcode_value}}

    def _score_ocr(self, ocr_texts: List[str]) -> List[Dict[str, Any]]:
        candidates = []
        for t in ocr_texts:
            res = self.repo.search_by_name(t)
            for p in res:
                # rough textual similarity: token overlap
                score = self._text_similarity(t, p.name)
                candidates.append({"product": p, "score": score, "component": "ocr", "details": {"ocr": t}})
        return candidates

    def _text_similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        a_tokens = set(a.lower().split())
        b_tokens = set(b.lower().split())
        inter = len(a_tokens & b_tokens)
        union = len(a_tokens | b_tokens)
        if union == 0:
            return 0.0
        return inter / union

    def _score_yolo(self, yolo_detections: List[dict]) -> List[Dict[str, Any]]:
        candidates = []
        for d in yolo_detections:
            cls = d.get("class_name")
            # look for products with yolo_class_mapping equal to class id
            prods = self.db.query(ProductModel).filter(ProductModel.yolo_class_mapping == d.get("class_id")).all()
            for p in prods:
                candidates.append({"product": p, "score": float(d.get("confidence", 0.0)), "component": "yolo", "details": {"yolo": d}})
        return candidates

    def _merge_candidates(self, candidates: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        merged = {}
        for c in candidates:
            pid = c["product"].id if c.get("product") else None
            if pid is None:
                continue
            entry = merged.setdefault(pid, {"product": c["product"], "scores": {}, "total": 0.0})
            comp = c.get("component")
            score = float(c.get("score") or 0.0)
            entry["scores"][comp] = max(entry["scores"].get(comp, 0.0), score)
        # compute weighted total
        for pid, entry in merged.items():
            total = 0.0
            for comp, sc in entry["scores"].items():
                w = self.weights.get(comp, 0.0)
                total += w * sc
            entry["total"] = total
        return merged

    def recognize(self, payload: dict) -> dict:
        # payload keys: yolo, ocr, barcode, embeddings, metadata, source_id
        barcodes = payload.get("barcode") or []
        ocrs = payload.get("ocr") or []
        yolo = payload.get("yolo") or []
        embeddings = payload.get("embeddings")

        # 1) Barcode priority
        for b in barcodes:
            val = b.get("value")
            if not val:
                continue
            res = self._score_barcode(val)
            if res:
                # create match with high confidence
                match = self.repo.create_match(product_id=res["product"].id, source_id=payload.get("source_id"), final_score=1.0, extras={"component":"barcode"})
                self.repo.add_candidate(match.id, res["product"].id, "barcode", 1.0, res.get("details"))
                self.repo.log_history(payload.get("source_id"), payload, match.id)
                return {"match_product_id": res["product"].id, "match_name": res["product"].name, "confidence": 1.0, "candidates": [{"product_id": res["product"].id, "name": res["product"].name, "score": 1.0, "component": "barcode"}], "reason": "barcode_exact"}

        # 2) OCR candidates
        ocr_texts = [o.get("text") for o in ocrs if o.get("text")]
        ocr_cands = self._score_ocr(ocr_texts)

        # 3) YOLO candidates
        yolo_cands = self._score_yolo(yolo)

        # 4) Merge and compute totals
        all_cands = ocr_cands + yolo_cands
        merged = self._merge_candidates(all_cands)
        # produce sorted list
        sorted_c = sorted(merged.values(), key=lambda e: e["total"], reverse=True)

        if not sorted_c:
            # unknown product
            u = self.repo.create_unknown(image_path=payload.get("metadata", {}).get("image_path"), ocr_text="; ".join(ocr_texts) if ocr_texts else None, barcode=barcodes[0].get("value") if barcodes else None, yolo_class=(yolo[0].get("class_name") if yolo else None), confidence=0.0, metadata=payload)
            self.repo.log_history(payload.get("source_id"), payload, None)
            return {"match_product_id": None, "match_name": None, "confidence": 0.0, "candidates": [], "reason": "unknown", "unknown_id": u.id}

        top = sorted_c[0]
        candidate_list = []
        for entry in sorted_c[:5]:
            p = entry["product"]
            candidate_list.append({"product_id": p.id, "name": p.name, "score": entry["total"], "component": ",".join(entry["scores"].keys())})

        match = self.repo.create_match(product_id=top["product"].id, source_id=payload.get("source_id"), final_score=top["total"], extras={"scores": top["scores"]})
        for entry in sorted_c[:5]:
            p = entry["product"]
            self.repo.add_candidate(match.id, p.id, "composite", entry["total"], {"scores": entry["scores"]})

        self.repo.log_history(payload.get("source_id"), payload, match.id)

        return {"match_product_id": top["product"].id, "match_name": top["product"].name, "confidence": top["total"], "candidates": candidate_list, "reason": "composite"}
