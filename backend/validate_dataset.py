from app.ml.dataset_validator import validate_dataset

# Validate the dataset
report = validate_dataset()

print(f"Validation OK: {report.ok}")
print(f"\nStatistics:")
for key, value in report.stats.items():
    print(f"  {key}: {value}")

print(f"\nIssues ({len(report.issues)}):")
for issue in report.issues:
    print(f"  [{issue.severity.upper()}] {issue.category}: {issue.message}")
    if issue.split:
        print(f"    Split: {issue.split}")
    if issue.file:
        print(f"    File: {issue.file}")
