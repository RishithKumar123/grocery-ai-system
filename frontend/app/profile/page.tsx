"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  User, 
  Mail, 
  Shield, 
  CheckCircle, 
  AlertTriangle, 
  ArrowLeft, 
  Loader2, 
  Save,
  Lock,
  Smartphone,
  Globe,
  Clock,
  Bell,
  Trash2,
  Tv
} from "lucide-react";
import { getAccessToken, getUserProfile, clearTokens, fetchWithAuth, setUserProfile } from "../../lib/auth";

export default function ProfilePage() {
  const router = useRouter();
  
  // Profile settings state
  const [profile, setProfile] = useState<any>(null);
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [lang, setLang] = useState("en");
  const [tz, setTz] = useState("UTC");
  const [notif, setNotif] = useState("email,sms,push");

  // Change Password state
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Active Sessions & Devices state
  const [sessions, setSessions] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);

  // Loaders & Alerts
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    const user = getUserProfile();

    if (!token || !user) {
      clearTokens();
      router.push("/login");
    } else {
      setProfile(user);
      setFullName(user.full_name || "");
      setPhone(user.phone_number || "");
      setLang(user.language || "en");
      setTz(user.timezone || "UTC");
      setNotif(user.notification_preferences || "email,sms,push");
      setLoading(false);
      
      // Load sessions and devices
      fetchSessions();
    }
  }, [router]);

  const fetchSessions = async () => {
    setSessionsLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/auth/sessions");
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
      }
      
      const devRes = await fetchWithAuth("/api/v1/auth/devices");
      if (devRes.ok) {
        const devData = await devRes.json();
        setDevices(devData);
      }
    } catch (err) {
      console.error("Failed to load active sessions / devices", err);
    } finally {
      setSessionsLoading(false);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await fetchWithAuth("/api/v1/auth/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName,
          phone_number: phone,
          language: lang,
          timezone: tz,
          notification_preferences: notif
        })
      });

      if (!res.ok) {
        throw new Error("Failed to update profile info.");
      }

      const updatedUser = await res.json();
      setUserProfile(updatedUser);
      setProfile(updatedUser);
      setSuccessMsg("Profile details updated successfully!");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setErrorMsg("New passwords do not match!");
      return;
    }

    setPasswordLoading(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await fetchWithAuth("/api/v1/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword
        })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to modify password.");
      }

      setSuccessMsg("Password changed successfully!");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update password.");
    } finally {
      setPasswordLoading(false);
    }
  };

  const terminateSession = async (id: number) => {
    setSuccessMsg(null);
    setErrorMsg(null);
    try {
      const res = await fetchWithAuth(`/api/v1/auth/session/${id}`, {
        method: "DELETE"
      });
      if (!res.ok) {
        throw new Error("Failed to terminate session.");
      }
      setSuccessMsg("Selected session was terminated successfully.");
      fetchSessions();
    } catch (err: any) {
      setErrorMsg(err.message || "Could not terminate session.");
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <span className="text-neutral-400 text-sm animate-pulse font-mono">Resolving profile credentials...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col px-4 py-12 text-neutral-100">
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-4xl mx-auto space-y-8 relative z-10">
        {/* Header Block */}
        <div className="flex items-center justify-between border-b border-neutral-900 pb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <User className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-2xl font-extrabold tracking-tight">Security & Settings</h2>
              <p className="text-xs text-neutral-500">Configure profile preferences and session locks</p>
            </div>
          </div>
          <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs text-neutral-400 hover:text-emerald-400 transition-colors font-bold">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
          </Link>
        </div>

        {/* Action alerts */}
        {successMsg && (
          <div className="p-4 rounded-2xl border border-emerald-500/20 bg-emerald-950/20 text-emerald-400 text-xs font-semibold">
            {successMsg}
          </div>
        )}
        {errorMsg && (
          <div className="p-4 rounded-2xl border border-red-500/20 bg-red-950/20 text-red-400 text-xs font-semibold">
            {errorMsg}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Column Left: General Settings */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* General Info Card */}
            <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-6">
              <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                <Globe className="w-4 h-4 text-emerald-400" /> Profile Configurations
              </h3>
              
              <form onSubmit={handleUpdateProfile} className="space-y-4 text-xs">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Full Name</label>
                    <input
                      type="text"
                      required
                      className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 focus:outline-none focus:border-emerald-500/40"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Phone Number</label>
                    <div className="relative">
                      <Smartphone className="absolute left-3 top-3 w-4 h-4 text-neutral-600" />
                      <input
                        type="text"
                        placeholder="+1 555-123-4567"
                        className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 focus:outline-none focus:border-emerald-500/40"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Language Preference</label>
                    <select
                      className="w-full px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 focus:outline-none focus:border-emerald-500/40"
                      value={lang}
                      onChange={(e) => setLang(e.target.value)}
                    >
                      <option value="en">English (US)</option>
                      <option value="es">Español</option>
                      <option value="fr">Français</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">System Timezone</label>
                    <select
                      className="w-full px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 focus:outline-none focus:border-emerald-500/40"
                      value={tz}
                      onChange={(e) => setTz(e.target.value)}
                    >
                      <option value="UTC">UTC (GMT+0)</option>
                      <option value="EST">Eastern Time (EST)</option>
                      <option value="IST">India Time (IST)</option>
                      <option value="PST">Pacific Time (PST)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Notification Channels</label>
                  <input
                    type="text"
                    className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 focus:outline-none focus:border-emerald-500/40"
                    value={notif}
                    onChange={(e) => setNotif(e.target.value)}
                  />
                  <span className="text-[10px] text-neutral-500 mt-1 block">Comma-separated: email, sms, push notifications</span>
                </div>

                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2.5 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold hover:bg-emerald-400 transition-colors disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
                >
                  {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />} Save Preferences
                </button>
              </form>
            </div>

            {/* Password Modification Form */}
            <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-6">
              <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                <Lock className="w-4 h-4 text-emerald-400" /> Change Security Password
              </h3>

              <form onSubmit={handleChangePassword} className="space-y-4 text-xs">
                <div>
                  <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Current Password</label>
                  <input
                    type="password"
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 focus:outline-none"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">New Password</label>
                    <input
                      type="password"
                      required
                      className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 focus:outline-none"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Confirm New Password</label>
                    <input
                      type="password"
                      required
                      className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 focus:outline-none"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={passwordLoading}
                  className="px-5 py-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 text-xs font-bold hover:bg-emerald-500/20 transition-colors disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
                >
                  {passwordLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Lock className="w-3.5 h-3.5" />} Modify Password
                </button>
              </form>
            </div>

            {/* Active Sessions & Devices Block */}
            <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-emerald-400" /> Active Session Logs
                </h3>
                <span className="text-[10px] text-neutral-500 font-mono">Devices: {devices.length}</span>
              </div>

              {sessionsLoading ? (
                <div className="text-center py-6 text-xs text-neutral-500 animate-pulse font-mono">Querying sessions...</div>
              ) : sessions.length === 0 ? (
                <div className="text-center py-6 text-xs text-neutral-500">No active refresh sessions.</div>
              ) : (
                <div className="space-y-3">
                  {devices.map((dev) => (
                    <div key={dev.id} className="p-4 rounded-2xl bg-neutral-950 border border-neutral-900 flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-neutral-900 text-emerald-400">
                          <Smartphone className="w-4 h-4" />
                        </div>
                        <div className="text-xs">
                          <span className="font-bold text-neutral-200 block">{dev.device_name}</span>
                          <span className="text-[10px] text-neutral-500 font-mono">Last Active: {new Date(dev.last_active).toLocaleString()}</span>
                        </div>
                      </div>
                      
                      <button 
                        onClick={() => terminateSession(dev.id)}
                        className="p-2 text-neutral-600 hover:text-red-400 hover:bg-neutral-900 rounded-xl transition-colors cursor-pointer"
                        title="Terminate Session"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>

          {/* Column Right: Security Overview Metadata */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* User credentials details */}
            <div className="p-5 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-6">
              <div>
                <h4 className="text-xs font-bold text-neutral-500 uppercase tracking-wider mb-2">Role Clearance</h4>
                <div className="flex items-center gap-2">
                  <Shield className="w-4.5 h-4.5 text-emerald-400" />
                  <span className="text-sm font-bold text-neutral-100">{profile.role}</span>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-neutral-500 uppercase tracking-wider mb-2">Account Status</h4>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4.5 h-4.5 text-emerald-400" />
                  <span className="text-xs text-neutral-300 font-medium">Activated & Verified</span>
                </div>
              </div>

              <div className="border-t border-neutral-900 pt-4 text-[10px] text-neutral-500 space-y-1 font-mono">
                <div>Client ID: #{profile.id}</div>
                <div>Created: {new Date(profile.created_at).toLocaleDateString()}</div>
                <div>Status: {profile.status}</div>
              </div>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
}
