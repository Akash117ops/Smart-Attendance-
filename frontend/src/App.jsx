import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  LayoutDashboard,
  ScanFace,
  Users,
  ListChecks,
  Building2,
  Calendar,
  BarChart3,
  Settings,
  UserCircle2,
  Plus,
  Search,
  Upload,
  X,
  CheckCircle2,
  ShieldCheck,
  Play,
  Square,
  TrendingUp,
  Clock,
  Loader2,
  ChevronRight,
  Fingerprint,
  Menu,
  ChevronDown,
  RefreshCw,
  AlertTriangle,
  Trash2,
} from "lucide-react";

import "./index.css";

/* =========================================================
   BACKEND
========================================================= */

const API_BASE_URL = "http://127.0.0.1:5000";

const DEFAULT_CLASSROOM_ID = 1;
const DEFAULT_PERIOD_NUMBER = 1;

/*
  Recognition is intentionally not performed
  on every webcam frame.
*/
const RECOGNITION_INTERVAL = 2500;

/* =========================================================
   NAVIGATION
========================================================= */

const NAV_ITEMS = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
  },
  {
    id: "live",
    label: "Live Attendance",
    icon: ScanFace,
  },
  {
    id: "students",
    label: "Students",
    icon: Users,
  },
  {
    id: "attendance",
    label: "Attendance",
    icon: ListChecks,
  },
  {
    id: "classrooms",
    label: "Classrooms",
    icon: Building2,
  },
  {
    id: "sessions",
    label: "Sessions",
    icon: Calendar,
  },
  {
    id: "reports",
    label: "Reports",
    icon: BarChart3,
  },
];

/* =========================================================
   FALLBACK UI DATA
========================================================= */

const LIVE_ROWS = [
  {
    name: "Aditi Sharma",
    usn: "1AM23IS001",
    status: "present",
    confidence: "98.6%",
    time: "09:12:04 AM",
  },
  {
    name: "Rohan Mehta",
    usn: "1AM23IS014",
    status: "present",
    confidence: "96.2%",
    time: "09:12:41 AM",
  },
  {
    name: "Unrecognized face",
    usn: "—",
    status: "unknown",
    confidence: "—",
    time: "09:13:07 AM",
  },
];

const RECENT_ROWS = [
  {
    name: "Aditi Sharma",
    usn: "1AM23IS001",
    date: "Aug 16, 2026",
    time: "09:12 AM",
    status: "present",
  },
  {
    name: "Karthik Rao",
    usn: "1AM23IS009",
    date: "Aug 16, 2026",
    time: "09:10 AM",
    status: "present",
  },
  {
    name: "Sneha Iyer",
    usn: "1AM23IS033",
    date: "Aug 15, 2026",
    time: "09:05 AM",
    status: "present",
  },
];

const VECTOR = [
  40, 65, 30, 80, 55, 20, 90, 45,
  60, 35, 75, 50, 25, 85, 40, 60,
  30, 70, 45, 55, 65, 35, 80, 50,
];

/* =========================================================
   PAGE META
========================================================= */

const PAGE_META = {
  dashboard: {
    title: "Faculty dashboard",
    sub: "Manage students, attendance and AI-powered classroom recognition.",
  },

  live: {
    title: "Live attendance",
    sub: "Monitor real-time recognition for the active classroom session.",
  },

  students: {
    title: "Students",
    sub: "Enrolled students and their facial recognition status.",
  },

  attendance: {
    title: "Attendance",
    sub: "Full attendance history across all classrooms.",
  },

  classrooms: {
    title: "Classrooms",
    sub: "Camera and layout configuration per classroom.",
  },

  sessions: {
    title: "Sessions",
    sub: "Scheduled and past class sessions.",
  },

  reports: {
    title: "Reports",
    sub: "Attendance analytics and exports.",
  },
};

/* =========================================================
   STATUS BADGE
========================================================= */

function StatusBadge({ status }) {
  const map = {
    present: {
      cls: "sa-badge-success",
      label: "Present",
    },

    enrolled: {
      cls: "sa-badge-success",
      label: "Enrolled",
    },

    active: {
      cls: "sa-badge-success",
      label: "Active",
    },

    unknown: {
      cls: "sa-badge-neutral",
      label: "Unknown",
    },

    pending: {
      cls: "sa-badge-warning",
      label: "Pending embedding",
    },

    spoof: {
      cls: "sa-badge-error",
      label: "Spoof detected",
    },
  };

  const item = map[status] || map.unknown;

  return (
    <span className={`sa-badge ${item.cls}`}>
      <span className="sa-badge-dot" />
      {item.label}
    </span>
  );
}

/* =========================================================
   CARD
========================================================= */

function Card({ children, style }) {
  return (
    <div className="sa-card" style={style}>
      {children}
    </div>
  );
}

/* =========================================================
   VECTOR VISUALIZATION
========================================================= */

function VectorViz() {
  return (
    <div>
      <div className="sa-vector-viz">
        {VECTOR.map((height, index) => (
          <div
            key={index}
            className="sa-vector-bar"
            style={{ height: `${height}%` }}
          />
        ))}
      </div>

      <div className="sa-vector-caption">
        Sample 512-d face embedding signature
      </div>
    </div>
  );
}

/* =========================================================
   DATE FORMATTER
========================================================= */

function formatDate(dateString) {
  if (!dateString) {
    return "—";
  }

  const parsedDate = new Date(dateString);

  if (Number.isNaN(parsedDate.getTime())) {
    return dateString;
  }

  return parsedDate.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

/* =========================================================
   CAMERA PANEL
========================================================= */

function CameraPanel({
  active,
  sessionLabel,
  videoRef,
  cameraError,
  recognitionResult,
  recognitionLoading,
}) {
  return (
    <div className="sa-camera-panel">
      <div className="sa-camera-frame">
        <div className="sa-camera-corner tl" />
        <div className="sa-camera-corner tr" />
        <div className="sa-camera-corner bl" />
        <div className="sa-camera-corner br" />

        {active && <div className="sa-scanline" />}

        {active ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              display: "block",
              borderRadius: 10,
              transform: "scaleX(-1)",
            }}
          />
        ) : (
          <div className="sa-camera-placeholder">
            <ScanFace
              size={22}
              style={{
                marginBottom: 8,
                opacity: 0.6,
              }}
            />

            <div>Camera is idle</div>
          </div>
        )}

        {cameraError && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: 20,
              textAlign: "center",
              background: "rgba(0,0,0,0.65)",
              color: "#fff",
              fontSize: 13,
            }}
          >
            {cameraError}
          </div>
        )}
      </div>

      <div className="sa-camera-meta">
        <span>Session</span>
        <strong>{sessionLabel}</strong>
      </div>

      <div className="sa-camera-meta">
        <span>Detector</span>
        <strong>FaceNet512</strong>
      </div>

      {recognitionLoading && (
        <div
          style={{
            marginTop: 10,
            padding: 10,
            borderRadius: 8,
            background: "#F3F4F6",
            color: "#6B7280",
            fontSize: 13,
            display: "flex",
            alignItems: "center",
            gap: 7,
          }}
        >
          <Loader2 size={14} className="sa-spin" />
          Recognizing face...
        </div>
      )}

      {recognitionResult?.type === "matched" && (
        <div
          style={{
            marginTop: 10,
            padding: 10,
            borderRadius: 8,
            background: "#ECFDF3",
            color: "#166534",
            fontSize: 13,
          }}
        >
          <strong>{recognitionResult.name}</strong>

          <br />

          {recognitionResult.alreadyMarked
            ? "Attendance already marked"
            : "Attendance marked"}
        </div>
      )}

      {recognitionResult?.type === "unknown" && (
        <div
          style={{
            marginTop: 10,
            padding: 10,
            borderRadius: 8,
            background: "#F3F4F6",
            color: "#6B7280",
            fontSize: 13,
          }}
        >
          {recognitionResult.message || "Unknown face"}
        </div>
      )}

      {recognitionResult?.type === "error" && (
        <div
          style={{
            marginTop: 10,
            padding: 10,
            borderRadius: 8,
            background: "#FEF2F2",
            color: "#B91C1C",
            fontSize: 13,
          }}
        >
          Recognition error
        </div>
      )}
    </div>
  );
}

/* =========================================================
   ADD STUDENT MODAL
========================================================= */

function AddStudentModal({ onClose, onSubmit }) {
  const [form, setForm] = useState({
    usn: "",
    name: "",
    email: "",
  });

  const [photos, setPhotos] = useState([]);
  const [dragging, setDragging] = useState(false);
  const [embedState, setEmbedState] = useState("idle");
  const [enrolling, setEnrolling] = useState(false);

  const fileInputRef = useRef(null);

  const addFiles = useCallback(
    (fileList) => {
      const files = Array.from(fileList || []).filter((file) =>
        file.type.startsWith("image/")
      );

      const available = Math.max(0, 5 - photos.length);

      const filesToAdd = files
        .slice(0, available)
        .map((file, index) => ({
          id: `${Date.now()}-${index}`,
          file,
          url: URL.createObjectURL(file),
        }));

      if (filesToAdd.length > 0) {
        setPhotos((previous) => [
          ...previous,
          ...filesToAdd,
        ]);

        setEmbedState("idle");
      }
    },
    [photos.length]
  );

  function removePhoto(id) {
    setPhotos((previous) =>
      previous.filter((photo) => photo.id !== id)
    );

    setEmbedState("idle");
  }

  const canEnroll =
    form.usn.trim() &&
    form.name.trim() &&
    photos.length >= 3;

  return (
    <div
      className="sa-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className="sa-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Add student"
      >
        <div className="sa-modal-head">
          <div>
            <p className="sa-modal-title">
              Add student
            </p>

            <p className="sa-modal-sub">
              Enroll a student into the AI
              attendance system.
            </p>
          </div>

          <button
            className="sa-modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <div className="sa-modal-body">
          <div className="sa-field-row">
            <div
              className="sa-field"
              style={{ marginBottom: 0 }}
            >
              <label className="sa-label">
                USN <span className="req">*</span>
              </label>

              <input
                className="sa-input"
                placeholder="1AM23IS0XX"
                value={form.usn}
                onChange={(event) =>
                  setForm((previous) => ({
                    ...previous,
                    usn: event.target.value,
                  }))
                }
              />
            </div>

            <div
              className="sa-field"
              style={{ marginBottom: 0 }}
            >
              <label className="sa-label">
                Student name{" "}
                <span className="req">*</span>
              </label>

              <input
                className="sa-input"
                placeholder="Full name"
                value={form.name}
                onChange={(event) =>
                  setForm((previous) => ({
                    ...previous,
                    name: event.target.value,
                  }))
                }
              />
            </div>
          </div>

          <div className="sa-field">
            <label className="sa-label">
              Email
            </label>

            <input
              className="sa-input"
              type="email"
              placeholder="student@amcec.edu"
              value={form.email}
              onChange={(event) =>
                setForm((previous) => ({
                  ...previous,
                  email: event.target.value,
                }))
              }
            />
          </div>

          <div
            className="sa-field"
            style={{ marginBottom: 0 }}
          >
            <label className="sa-label">
              Face photos{" "}
              <span className="req">*</span>
            </label>

            <div
              className={`sa-dropzone ${
                dragging ? "drag" : ""
              }`}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => {
                setDragging(false);
              }}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                addFiles(event.dataTransfer.files);
              }}
              onClick={() =>
                fileInputRef.current?.click()
              }
              role="button"
              tabIndex={0}
            >
              <div className="sa-dropzone-icon">
                <Upload size={17} />
              </div>

              <div className="sa-dropzone-title">
                Upload student face photos
              </div>

              <div className="sa-dropzone-sub">
                Drag and drop, or{" "}
                <span className="sa-dropzone-link">
                  browse files
                </span>{" "}
                · 4–5 clear photos from different
                angles
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                hidden
                onChange={(event) => {
                  addFiles(event.target.files);
                  event.target.value = "";
                }}
              />
            </div>

            {photos.length > 0 && (
              <div className="sa-thumb-grid">
                {photos.map((photo) => (
                  <div
                    key={photo.id}
                    className="sa-thumb"
                  >
                    <img
                      src={photo.url}
                      alt="Uploaded face"
                    />

                    <button
                      className="sa-thumb-remove"
                      onClick={(event) => {
                        event.stopPropagation();
                        removePhoto(photo.id);
                      }}
                      aria-label="Remove photo"
                    >
                      <X size={10} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <p className="sa-helper">
              {photos.length}/5 photos added
              {photos.length < 3
                ? " · at least 3 needed to generate an embedding"
                : ""}
            </p>

            <div className="sa-embed-box">
              <div className="sa-embed-row">
                <span className="sa-embed-label">
                  <Fingerprint size={15} />
                  Face embedding · FaceNet512
                </span>

                {embedState === "generating" && (
                  <span className="sa-embed-status">
                    <Loader2
                      size={13}
                      className="sa-spin"
                      style={{
                        verticalAlign: "-2px",
                        marginRight: 4,
                      }}
                    />
                    Generating…
                  </span>
                )}

                {embedState === "done" && (
                  <span className="sa-embed-status done">
                    <CheckCircle2
                      size={13}
                      style={{
                        verticalAlign: "-2px",
                        marginRight: 4,
                      }}
                    />
                    512-dim vector ready
                  </span>
                )}

                {embedState === "idle" && (
                  <span className="sa-embed-status">
                    Generated automatically during
                    enrollment
                  </span>
                )}
              </div>

              <p
                className="sa-helper"
                style={{
                  marginTop: 2,
                  marginBottom: 0,
                }}
              >
                The backend processes the uploaded
                photos using FaceNet512 and stores
                the 512-dimensional embedding in
                MySQL.
              </p>
            </div>
          </div>
        </div>

        <div className="sa-modal-footer">
          <button
            className="sa-btn sa-btn-secondary sa-btn-sm"
            onClick={onClose}
          >
            Cancel
          </button>

          <button
            className="sa-btn sa-btn-primary sa-btn-sm"
            disabled={!canEnroll || enrolling}
            onClick={async () => {
              setEnrolling(true);
              setEmbedState("generating");

              try {
                await onSubmit({
                  ...form,
                  photos,
                });

                setEmbedState("done");
              } catch (error) {
                setEmbedState("idle");
              } finally {
                setEnrolling(false);
              }
            }}
          >
            {enrolling ? (
              <>
                <Loader2
                  size={14}
                  className="sa-spin"
                />
                Generating FaceNet512...
              </>
            ) : (
              <>
                <Fingerprint size={14} />
                Enroll student
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   LIVE ATTENDANCE SECTION
========================================================= */

function LiveAttendanceSection({
  sessionActive,
  sessionId,
  onStart,
  onStop,
  compact,
  recognitionResult,
  recognitionLoading,
  cameraError,
  videoRef,
}) {
  const hasRecognition =
    recognitionResult && recognitionResult.type;

  return (
    <Card>
      <div className="sa-card-head">
        <div className="sa-card-title-row">
          <div
            className={`sa-card-icon-wrap ${
              sessionActive ? "success" : "accent"
            }`}
          >
            <ScanFace size={16} />
          </div>

          <div>
            <p className="sa-card-title">
              Live attendance
            </p>

            <p className="sa-card-desc">
              Classroom recognition and automatic
              attendance marking.
            </p>
          </div>
        </div>

        {sessionActive ? (
          <span className="sa-badge sa-badge-success">
            <span className="sa-badge-dot" />
            Session active
          </span>
        ) : (
          <span className="sa-badge sa-badge-neutral">
            <span className="sa-badge-dot" />
            Session inactive
          </span>
        )}
      </div>

      <div className="sa-live-grid">
        <CameraPanel
          active={sessionActive}
          sessionLabel={
            sessionActive
              ? `Session #${sessionId}`
              : "None"
          }
          videoRef={videoRef}
          cameraError={cameraError}
          recognitionResult={recognitionResult}
          recognitionLoading={recognitionLoading}
        />

        <div>
          <div className="sa-table-wrap">
            <table className="sa-table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>USN</th>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Time</th>
                </tr>
              </thead>

              <tbody>
                {hasRecognition ? (
                  <tr>
                    <td className="sa-cell-name">
                      {recognitionResult.name}
                    </td>

                    <td className="sa-cell-muted">
                      {recognitionResult.usn || "—"}
                    </td>

                    <td>
                      <StatusBadge
                        status={
                          recognitionResult.type ===
                          "matched"
                            ? "present"
                            : recognitionResult.type ===
                              "unknown"
                            ? "unknown"
                            : "pending"
                        }
                      />
                    </td>

                    <td className="sa-cell-muted">
                      {recognitionResult.confidence !==
                      null
                        ? `${recognitionResult.confidence.toFixed(
                            1
                          )}%`
                        : "—"}
                    </td>

                    <td className="sa-cell-muted">
                      {recognitionResult.time || "—"}
                    </td>
                  </tr>
                ) : (
                  (compact
                    ? LIVE_ROWS.slice(0, 3)
                    : LIVE_ROWS
                  ).map((row, index) => (
                    <tr key={index}>
                      <td className="sa-cell-name">
                        {sessionActive
                          ? "Waiting for recognition..."
                          : row.name}
                      </td>

                      <td className="sa-cell-muted">
                        {sessionActive ? "—" : row.usn}
                      </td>

                      <td>
                        {sessionActive ? (
                          <StatusBadge status="pending" />
                        ) : (
                          <StatusBadge
                            status={row.status}
                          />
                        )}
                      </td>

                      <td className="sa-cell-muted">
                        {sessionActive
                          ? "—"
                          : row.confidence}
                      </td>

                      <td className="sa-cell-muted">
                        {sessionActive
                          ? "—"
                          : row.time}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {recognitionLoading && (
            <div
              style={{
                marginTop: 10,
                fontSize: 12,
                color: "var(--text-tertiary)",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <Loader2 size={13} className="sa-spin" />
              Recognizing face...
            </div>
          )}

          {recognitionResult?.message && (
            <div
              style={{
                marginTop: 10,
                fontSize: 12,
                color: "var(--text-secondary)",
              }}
            >
              {recognitionResult.message}
            </div>
          )}

          <div
            className="sa-card-actions"
            style={{ marginTop: 12 }}
          >
            {sessionActive ? (
              <button
                className="sa-btn sa-btn-danger sa-btn-sm"
                onClick={onStop}
              >
                <Square size={13} />
                Stop session
              </button>
            ) : (
              <button
                className="sa-btn sa-btn-primary sa-btn-sm"
                onClick={onStart}
              >
                <Play size={13} />
                Start session
              </button>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

/* =========================================================
   ATTENDANCE VIEW
========================================================= */

function AttendanceView({
  attendance,
  loading,
  error,
  onRefresh,
}) {
  const [query, setQuery] = useState("");

  const filtered = attendance.filter((record) => {
    const search = query.toLowerCase();

    return (
      String(record.name || "")
        .toLowerCase()
        .includes(search) ||
      String(record.usn || "")
        .toLowerCase()
        .includes(search) ||
      String(record.date || "")
        .toLowerCase()
        .includes(search)
    );
  });

  return (
    <Card style={{ marginBottom: 0 }}>
      <div className="sa-toolbar">
        <div className="sa-search">
          <Search size={15} />

          <input
            placeholder="Search by name or USN"
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
          />
        </div>

        <button
          className="sa-btn sa-btn-secondary"
          onClick={onRefresh}
          disabled={loading}
        >
          <RefreshCw
            size={14}
            className={loading ? "sa-spin" : ""}
          />
          Refresh
        </button>
      </div>

      {error && (
        <div
          style={{
            padding: "12px 14px",
            marginBottom: 14,
            borderRadius: 8,
            background: "#FDEEEE",
            color: "#DC2626",
            fontSize: 13,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <AlertTriangle size={15} />
          {error}
        </div>
      )}

      <div className="sa-table-wrap">
        <table className="sa-table">
          <thead>
            <tr>
              <th>Student</th>
              <th>USN</th>
              <th>Date</th>
              <th>Time</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {loading && (
              <tr>
                <td
                  colSpan={5}
                  style={{
                    textAlign: "center",
                    padding: 30,
                  }}
                >
                  <Loader2
                    size={20}
                    className="sa-spin"
                    style={{
                      verticalAlign: "middle",
                      marginRight: 8,
                    }}
                  />
                  Loading attendance...
                </td>
              </tr>
            )}

            {!loading &&
              filtered.map((record, index) => (
                <tr key={record.attendance_id || index}>
                  <td className="sa-cell-name">
                    {record.name ||
                      record.student_name ||
                      "Unknown"}
                  </td>

                  <td className="sa-cell-muted">
                    {record.usn || "—"}
                  </td>

                  <td className="sa-cell-muted">
                    {formatDate(
                      record.date ||
                        record.attendance_date ||
                        record.created_at
                    )}
                  </td>

                  <td className="sa-cell-muted">
                    {record.time ||
                      record.attendance_time ||
                      "—"}
                  </td>

                  <td>
                    <StatusBadge
                      status={
                        record.status === "absent"
                          ? "unknown"
                          : "present"
                      }
                    />
                  </td>
                </tr>
              ))}

            {!loading &&
              filtered.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="sa-cell-muted"
                    style={{
                      textAlign: "center",
                      padding: "30px 0",
                    }}
                  >
                    {query
                      ? `No attendance records match "${query}".`
                      : "No attendance records found."}
                  </td>
                </tr>
              )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/* =========================================================
   DASHBOARD
========================================================= */

function DashboardView({
  students,
  studentsLoading,
  sessionActive,
  sessionId,
  onStart,
  onStop,
  onAddStudent,
  onViewStudents,
  onRefreshStudents,
  recognitionResult,
  recognitionLoading,
  cameraError,
  videoRef,
  dashboardData,
  attendance,
}) {
  const totalStudents =
    dashboardData?.total_students ??
    students.length;

  const todayAttendance =
    dashboardData?.today_attendance ??
    dashboardData?.today_present ??
    attendance.filter((record) => {
      const today = new Date().toDateString();

      const dateValue =
        record.date ||
        record.attendance_date ||
        record.created_at;

      if (!dateValue) return false;

      return (
        new Date(dateValue).toDateString() ===
        today
      );
    }).length;

  const attendanceRate =
    dashboardData?.attendance_rate ??
    dashboardData?.today_attendance_rate ??
    null;

  return (
    <>
      <div className="sa-stats-grid">
        <div className="sa-stat-card">
          <div className="sa-stat-top">
            <span className="sa-stat-label">
              Total Students
            </span>

            <div className="sa-stat-icon-wrap">
              <Users size={14} />
            </div>
          </div>

          <div className="sa-stat-value">
            {studentsLoading
              ? "..."
              : totalStudents}
          </div>

          <div className="sa-stat-trend positive">
            Live from database
          </div>
        </div>

        <div className="sa-stat-card">
          <div className="sa-stat-top">
            <span className="sa-stat-label">
              Today's Attendance
            </span>

            <div className="sa-stat-icon-wrap">
              <CheckCircle2 size={14} />
            </div>
          </div>

          <div className="sa-stat-value">
            {todayAttendance}
          </div>

          <div className="sa-stat-trend">
            Attendance records today
          </div>
        </div>

        <div className="sa-stat-card">
          <div className="sa-stat-top">
            <span className="sa-stat-label">
              Active Session
            </span>

            <div className="sa-stat-icon-wrap">
              <ScanFace size={14} />
            </div>
          </div>

          <div className="sa-stat-value">
            {sessionActive
              ? "ACTIVE"
              : "IDLE"}
          </div>

          <div className="sa-stat-trend">
            {sessionActive
              ? `Session #${sessionId}`
              : "No active session"}
          </div>
        </div>

        <div className="sa-stat-card">
          <div className="sa-stat-top">
            <span className="sa-stat-label">
              Attendance Rate
            </span>

            <div className="sa-stat-icon-wrap">
              <TrendingUp size={14} />
            </div>
          </div>

          <div className="sa-stat-value">
            {attendanceRate !== null &&
            attendanceRate !== undefined
              ? `${Number(attendanceRate).toFixed(1)}%`
              : "—"}
          </div>

          <div className="sa-stat-trend">
            Based on attendance records
          </div>
        </div>
      </div>

      <div className="sa-section-grid">
        <Card style={{ marginBottom: 0 }}>
          <div className="sa-card-head">
            <div className="sa-card-title-row">
              <div className="sa-card-icon-wrap accent">
                <Users size={16} />
              </div>

              <div>
                <p className="sa-card-title">
                  Student management
                </p>

                <p className="sa-card-desc">
                  Register and manage students
                  enrolled in the AI attendance
                  system.
                </p>
              </div>
            </div>
          </div>

          <div className="sa-card-actions">
            <button
              className="sa-btn sa-btn-primary"
              onClick={onAddStudent}
            >
              <Plus size={14} />
              Add student
            </button>

            <button
              className="sa-btn sa-btn-secondary"
              onClick={onViewStudents}
            >
              View students
            </button>

            <button
              className="sa-btn sa-btn-ghost"
              onClick={onRefreshStudents}
              title="Refresh students"
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </Card>

        <Card style={{ marginBottom: 0 }}>
          <div className="sa-card-head">
            <div className="sa-card-title-row">
              <div className="sa-card-icon-wrap success">
                <ShieldCheck size={16} />
              </div>

              <div>
                <p className="sa-card-title">
                  Anti-spoofing
                </p>

                <p className="sa-card-desc">
                  AI-powered liveness detection
                  prevents attendance from being
                  recorded using photographs or
                  screens.
                </p>
              </div>
            </div>
          </div>

          <span className="sa-badge sa-badge-success">
            <span className="sa-badge-dot" />
            Protection active
          </span>
        </Card>
      </div>

      <Card>
        <div className="sa-card-head">
          <div className="sa-card-title-row">
            <div className="sa-card-icon-wrap accent">
              <Fingerprint size={16} />
            </div>

            <div>
              <p className="sa-card-title">
                AI face recognition
              </p>

              <p className="sa-card-desc">
                Real-time classroom recognition
                against enrolled student
                embeddings.
              </p>
            </div>
          </div>

          <button
            className="sa-btn sa-btn-primary"
            onClick={onStart}
            disabled={sessionActive}
          >
            <Play size={14} />

            {sessionActive
              ? "Session running"
              : "Start live attendance"}
          </button>
        </div>

        <div className="sa-tech-grid">
          <div className="sa-tech-item">
            <div className="sa-tech-label">
              Model
            </div>

            <div className="sa-tech-value">
              FaceNet512
            </div>
          </div>

          <div className="sa-tech-item">
            <div className="sa-tech-label">
              Status
            </div>

            <div
              className="sa-tech-value"
              style={{
                color: sessionActive
                  ? "var(--success)"
                  : "var(--text-primary)",
              }}
            >
              {sessionActive
                ? "Running"
                : "Idle"}
            </div>
          </div>

          <div className="sa-tech-item">
            <div className="sa-tech-label">
              Threshold
            </div>

            <div className="sa-tech-value">
              0.40 cosine distance
            </div>
          </div>

          <div className="sa-tech-item">
            <div className="sa-tech-label">
              Enrolled
            </div>

            <div className="sa-tech-value">
              {studentsLoading
                ? "..."
                : `${students.length} students`}
            </div>
          </div>
        </div>

        <VectorViz />
      </Card>

      <LiveAttendanceSection
        sessionActive={sessionActive}
        sessionId={sessionId}
        onStart={onStart}
        onStop={onStop}
        compact
        recognitionResult={recognitionResult}
        recognitionLoading={recognitionLoading}
        cameraError={cameraError}
        videoRef={videoRef}
      />

      <Card style={{ marginBottom: 0 }}>
        <div className="sa-card-head">
          <div className="sa-card-title-row">
            <div className="sa-card-icon-wrap accent">
              <Clock size={16} />
            </div>

            <div>
              <p className="sa-card-title">
                Recent attendance
              </p>

              <p className="sa-card-desc">
                Latest recorded check-ins
                across your classrooms.
              </p>
            </div>
          </div>

          <button
            className="sa-btn sa-btn-secondary sa-btn-sm"
            onClick={onViewStudents}
          >
            View students
            <ChevronRight size={13} />
          </button>
        </div>

        <div className="sa-table-wrap">
          <table className="sa-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>USN</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {attendance.length > 0
                ? attendance
                    .slice(0, 5)
                    .map((row, index) => (
                      <tr
                        key={
                          row.attendance_id ||
                          index
                        }
                      >
                        <td className="sa-cell-name">
                          {row.name ||
                            row.student_name ||
                            "Unknown"}
                        </td>

                        <td className="sa-cell-muted">
                          {row.usn || "—"}
                        </td>

                        <td className="sa-cell-muted">
                          {formatDate(
                            row.date ||
                              row.attendance_date ||
                              row.created_at
                          )}
                        </td>

                        <td className="sa-cell-muted">
                          {row.time ||
                            row.attendance_time ||
                            "—"}
                        </td>

                        <td>
                          <StatusBadge
                            status="present"
                          />
                        </td>
                      </tr>
                    ))
                : RECENT_ROWS.map(
                    (row, index) => (
                      <tr key={index}>
                        <td className="sa-cell-name">
                          {row.name}
                        </td>

                        <td className="sa-cell-muted">
                          {row.usn}
                        </td>

                        <td className="sa-cell-muted">
                          {row.date}
                        </td>

                        <td className="sa-cell-muted">
                          {row.time}
                        </td>

                        <td>
                          <StatusBadge
                            status={row.status}
                          />
                        </td>
                      </tr>
                    )
                  )}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}

/* =========================================================
   STUDENTS VIEW
========================================================= */

function StudentsView({
  students,
  loading,
  error,
  onAddStudent,
  onRefresh,
  onDeleteStudent,
  deletingId,
}) {
  const [query, setQuery] = useState("");

  const filtered = students.filter((student) => {
    const search = query.toLowerCase();

    return (
      student.name
        ?.toLowerCase()
        .includes(search) ||
      student.usn
        ?.toLowerCase()
        .includes(search) ||
      student.email
        ?.toLowerCase()
        .includes(search)
    );
  });

  return (
    <Card style={{ marginBottom: 0 }}>
      <div className="sa-toolbar">
        <div className="sa-search">
          <Search size={15} />

          <input
            placeholder="Search by name or USN"
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
          />
        </div>

        <div
          className="sa-card-actions"
          style={{ marginLeft: "auto" }}
        >
          <button
            className="sa-btn sa-btn-secondary"
            onClick={onRefresh}
            disabled={loading}
          >
            <RefreshCw
              size={14}
              className={
                loading ? "sa-spin" : ""
              }
            />
            Refresh
          </button>

          <button
            className="sa-btn sa-btn-primary"
            onClick={onAddStudent}
          >
            <Plus size={14} />
            Add student
          </button>
        </div>
      </div>

      {error && (
        <div
          style={{
            padding: "12px 14px",
            marginBottom: 14,
            borderRadius: 8,
            background: "#FDEEEE",
            color: "#DC2626",
            fontSize: 13,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <AlertTriangle size={15} />
          {error}
        </div>
      )}

      <div className="sa-table-wrap">
        <table className="sa-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Student</th>
              <th>USN</th>
              <th>Email</th>
              <th>Enrolled</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {loading && (
              <tr>
                <td
                  colSpan={7}
                  style={{
                    textAlign: "center",
                    padding: 30,
                  }}
                >
                  <Loader2
                    size={20}
                    className="sa-spin"
                    style={{
                      verticalAlign: "middle",
                      marginRight: 8,
                    }}
                  />
                  Loading students...
                </td>
              </tr>
            )}

            {!loading &&
              filtered.map((student) => (
                <tr
                  key={student.student_id}
                >
                  <td className="sa-cell-muted">
                    #{student.student_id}
                  </td>

                  <td className="sa-cell-name">
                    {student.name}
                  </td>

                  <td className="sa-cell-muted">
                    {student.usn}
                  </td>

                  <td className="sa-cell-muted">
                    {student.email || "—"}
                  </td>

                  <td className="sa-cell-muted">
                    {formatDate(
                      student.enrollment_date
                    )}
                  </td>

                  <td>
                    <StatusBadge
                      status={
                        student.status ||
                        "active"
                      }
                    />
                  </td>

                  <td>
                    <button
                      className="sa-btn sa-btn-danger sa-btn-sm"
                      onClick={() =>
                        onDeleteStudent(student)
                      }
                      disabled={
                        deletingId ===
                        student.student_id
                      }
                      title={`Delete ${student.name}`}
                    >
                      {deletingId ===
                      student.student_id ? (
                        <Loader2
                          size={13}
                          className="sa-spin"
                        />
                      ) : (
                        <Trash2 size={13} />
                      )}
                      Delete
                    </button>
                  </td>
                </tr>
              ))}

            {!loading &&
              filtered.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="sa-cell-muted"
                    style={{
                      textAlign: "center",
                      padding: "30px 0",
                    }}
                  >
                    {query
                      ? `No students match "${query}".`
                      : "No students found in database."}
                  </td>
                </tr>
              )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
// ============================================================
// REPORTS VIEW — MONTHLY REPORTS
// ============================================================

function ReportsView() {

  const [month, setMonth] = useState(
    new Date().getMonth() + 1
  );

  const [year, setYear] = useState(
    new Date().getFullYear()
  );

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function loadReport() {

    try {

      setLoading(true);
      setError('');

      const response = await fetch(
        `${API_BASE_URL}/api/reports/monthly?month=${month}&year=${year}`
      );

      if (!response.ok) {
        throw new Error(
          `Server returned ${response.status}`
        );
      }

      const data = await response.json();

      setReport(data);

    } catch (error) {

      console.error(
        'Failed to load monthly report:',
        error
      );

      setError(
        'Unable to load monthly report.'
      );

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {

    loadReport();

  }, [month, year]);


  return (

    <Card style={{ marginBottom: 0 }}>

      <div className="sa-toolbar">

        <div>

          <p className="sa-card-title">
            Monthly attendance report
          </p>

          <p className="sa-card-desc">
            Attendance summary for the selected month.
          </p>

        </div>


        <div
          style={{
            display: 'flex',
            gap: 8,
            alignItems: 'center'
          }}
        >

          <select
            className="sa-input"
            value={month}
            onChange={(event) =>
              setMonth(Number(event.target.value))
            }
            style={{ width: 130 }}
          >

            {[
              'January',
              'February',
              'March',
              'April',
              'May',
              'June',
              'July',
              'August',
              'September',
              'October',
              'November',
              'December'
            ].map((name, index) => (

              <option
                key={index + 1}
                value={index + 1}
              >
                {name}
              </option>

            ))}

          </select>


          <select
            className="sa-input"
            value={year}
            onChange={(event) =>
              setYear(Number(event.target.value))
            }
            style={{ width: 100 }}
          >

            <option value={2026}>
              2026
            </option>

            <option value={2027}>
              2027
            </option>

          </select>

        </div>

      </div>


      {loading && (

        <div
          style={{
            textAlign: 'center',
            padding: 50,
            color: 'var(--text-secondary)'
          }}
        >

          <Loader2
            size={25}
            className="sa-spin"
          />

          <div style={{ marginTop: 10 }}>
            Loading monthly report...
          </div>

        </div>

      )}


      {error && (

        <div
          style={{
            padding: 20,
            color: 'var(--error)'
          }}
        >
          {error}
        </div>

      )}


      {!loading && !error && report && (

        <div>

          {/* SUMMARY */}

          <div className="sa-stats-grid">

            <div className="sa-stat-card">

              <div className="sa-stat-label">
                Month
              </div>

              <div className="sa-stat-value">
                {report.month || month}
              </div>

            </div>


            <div className="sa-stat-card">

              <div className="sa-stat-label">
                Total Students
              </div>

              <div className="sa-stat-value">
                {report.total_students ?? 0}
              </div>

            </div>


            <div className="sa-stat-card">

              <div className="sa-stat-label">
                Total Attendance
              </div>

              <div className="sa-stat-value">
                {report.total_attendance ?? 0}
              </div>

            </div>


            <div className="sa-stat-card">

              <div className="sa-stat-label">
                Attendance Rate
              </div>

              <div className="sa-stat-value">
                {report.attendance_rate ?? 0}%
              </div>

            </div>

          </div>


          {/* STUDENT REPORT */}

          {Array.isArray(report.students) && (

            <div className="sa-table-wrap">

              <table className="sa-table">

                <thead>

                  <tr>
                    <th>Student</th>
                    <th>USN</th>
                    <th>Present</th>
                    <th>Total Sessions</th>
                    <th>Attendance %</th>
                  </tr>

                </thead>


                <tbody>

                  {report.students.map(
                    (student, index) => (

                      <tr key={
                        student.student_id || index
                      }>

                        <td className="sa-cell-name">
                          {student.name}
                        </td>

                        <td className="sa-cell-muted">
                          {student.usn}
                        </td>

                        <td>
                          {student.present ?? 0}
                        </td>

                        <td className="sa-cell-muted">
                          {student.total_sessions ?? 0}
                        </td>

                        <td>

                          <span className="sa-badge sa-badge-success">

                            <span className="sa-badge-dot" />

                            {student.attendance_percentage ??
                              student.attendance_rate ??
                              0}%

                          </span>

                        </td>

                      </tr>

                    )
                  )}


                  {report.students.length === 0 && (

                    <tr>

                      <td
                        colSpan={5}
                        style={{
                          textAlign: 'center',
                          padding: 35
                        }}
                        className="sa-cell-muted"
                      >
                        No attendance records found
                        for this month.
                      </td>

                    </tr>

                  )}

                </tbody>

              </table>

            </div>

          )}

        </div>

      )}

    </Card>
  );
}
/* =========================================================
   EMPTY VIEWS
========================================================= */

const EMPTY_CONTENT = {
  classrooms: {
    icon: Building2,
    title: "Classrooms",
    sub: "Manage classroom information and camera configuration.",
    cta: "Add a classroom",
  },

  sessions: {
    icon: Calendar,
    title: "Sessions",
    sub: "Manage classroom attendance sessions and timings.",
    cta: "Create a session",
  },

  reports: {
    icon: BarChart3,
    title: "Reports",
    sub: "Monthly attendance reports will be connected here.",
    cta: "Generate report",
  },
};

function EmptyView({ nav }) {
  const content = EMPTY_CONTENT[nav];

  if (!content) {
    return null;
  }

  const Icon = content.icon;

  return (
    <Card style={{ marginBottom: 0 }}>
      <div className="sa-empty">
        <div className="sa-empty-icon">
          <Icon size={20} />
        </div>

        <div className="sa-empty-title">
          {content.title}
        </div>

        <p className="sa-empty-sub">
          {content.sub}
        </p>

        <button
          className="sa-btn sa-btn-secondary sa-btn-sm"
          style={{ margin: "0 auto" }}
        >
          {content.cta}
        </button>
      </div>
    </Card>
  );
}

/* =========================================================
   MAIN APP
========================================================= */

export default function SmartAttendanceDashboard() {
  const [activeNav, setActiveNav] =
    useState("dashboard");

  const [mobileNavOpen, setMobileNavOpen] =
    useState(false);

  const [modalOpen, setModalOpen] =
    useState(false);

  const [sessionActive, setSessionActive] =
    useState(false);

  const [sessionId, setSessionId] =
    useState(null);

  /* =====================================================
     STUDENTS
  ===================================================== */

  const [students, setStudents] =
    useState([]);

  const [studentsLoading, setStudentsLoading] =
    useState(true);

  const [studentsError, setStudentsError] =
    useState("");

  const [deletingStudentId, setDeletingStudentId] =
    useState(null);

  /* =====================================================
     DASHBOARD
  ===================================================== */

  const [dashboardData, setDashboardData] =
    useState(null);

  /* =====================================================
     ATTENDANCE
  ===================================================== */

  const [attendance, setAttendance] =
    useState([]);

  const [attendanceLoading, setAttendanceLoading] =
    useState(false);

  const [attendanceError, setAttendanceError] =
    useState("");

  /* =====================================================
     TOAST
  ===================================================== */

  const [toast, setToast] =
    useState(null);

  /* =====================================================
     SINGLE CAMERA PIPELINE
  ===================================================== */

  const videoRef = useRef(null);

  const streamRef = useRef(null);

  const recognitionTimerRef =
    useRef(null);

  const recognitionBusyRef =
    useRef(false);

  const [cameraError, setCameraError] =
    useState("");

  const [recognitionLoading, setRecognitionLoading] =
    useState(false);

  const [recognitionResult, setRecognitionResult] =
    useState(null);

  /* =====================================================
     FETCH STUDENTS
  ===================================================== */

  const fetchStudents =
    useCallback(async () => {
      try {
        setStudentsLoading(true);
        setStudentsError("");

        const response = await fetch(
          `${API_BASE_URL}/api/students`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.message ||
              `Server returned ${response.status}`
          );
        }

        setStudents(
          Array.isArray(data.students)
            ? data.students
            : []
        );
      } catch (error) {
        console.error(
          "Failed to fetch students:",
          error
        );

        setStudentsError(
          "Unable to connect to the backend. Make sure Flask is running on port 5000."
        );
      } finally {
        setStudentsLoading(false);
      }
    }, []);

  /* =====================================================
     FETCH DASHBOARD
  ===================================================== */

  const fetchDashboard =
    useCallback(async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/dashboard`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.message ||
              "Failed to load dashboard."
          );
        }

        setDashboardData(data);
      } catch (error) {
        /*
          Dashboard endpoint may not exist yet.
          Do not break the whole frontend if it
          isn't available.
        */
        console.warn(
          "Dashboard endpoint unavailable:",
          error.message
        );

        setDashboardData(null);
      }
    }, []);

  /* =====================================================
     FETCH ATTENDANCE
  ===================================================== */

  const fetchAttendance =
    useCallback(async () => {
      try {
        setAttendanceLoading(true);
        setAttendanceError("");

        const response = await fetch(
          `${API_BASE_URL}/api/attendance`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.message ||
              "Failed to load attendance."
          );
        }

        setAttendance(
          Array.isArray(data.attendance)
            ? data.attendance
            : []
        );
      } catch (error) {
        console.error(
          "Failed to fetch attendance:",
          error
        );

        setAttendanceError(
          "Unable to load attendance records."
        );
      } finally {
        setAttendanceLoading(false);
      }
    }, []);

  /* =====================================================
     INITIAL LOAD
  ===================================================== */

  useEffect(() => {
    fetchStudents();
    fetchDashboard();
    fetchAttendance();
  }, [
    fetchStudents,
    fetchDashboard,
    fetchAttendance,
  ]);

  /* =====================================================
     NAVIGATION
  ===================================================== */

  function go(id) {
    setActiveNav(id);
    setMobileNavOpen(false);

    /*
      Refresh attendance whenever the
      attendance page is opened.
    */
    if (id === "attendance") {
      fetchAttendance();
    }

    if (id === "dashboard") {
      fetchDashboard();
      fetchAttendance();
    }
  }

  /* =====================================================
     TOAST
  ===================================================== */

  function showToast(message) {
    setToast(message);

    setTimeout(() => {
      setToast(null);
    }, 3000);
  }

  /* =====================================================
     ENROLL STUDENT
  ===================================================== */

  async function handleEnroll(student) {
    try {
      setModalOpen(false);

      showToast(
        "Generating FaceNet512 embedding..."
      );

      const formData = new FormData();

      formData.append(
        "usn",
        student.usn
      );

      formData.append(
        "name",
        student.name
      );

      formData.append(
        "email",
        student.email || ""
      );

      student.photos.forEach((photo) => {
        formData.append(
          "photos",
          photo.file
        );
      });

      const response = await fetch(
        `${API_BASE_URL}/api/students/enroll`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.message ||
            "Enrollment failed."
        );
      }

      console.log(
        "ENROLLMENT SUCCESS:",
        data
      );

      showToast(
        `${student.name} enrolled successfully — 512-d embedding saved.`
      );

      await fetchStudents();
      await fetchDashboard();
    } catch (error) {
      console.error(
        "Enrollment error:",
        error
      );

      showToast(
        `Enrollment failed: ${error.message}`
      );

      throw error;
    }
  }

  /* =====================================================
     DELETE STUDENT
     
     Removes the student from MySQL via the Flask
     backend, then updates the dashboard state so
     the row disappears immediately.
  ===================================================== */

  async function handleDeleteStudent(student) {
    const confirmed = window.confirm(
      `Delete ${student.name} (${student.usn})? This will permanently remove the student and their face embedding from the database.`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingStudentId(student.student_id);

      const response = await fetch(
        `${API_BASE_URL}/api/students/${student.student_id}`,
        {
          method: "DELETE",
        }
      );

      let data = {};

      try {
        data = await response.json();
      } catch (parseError) {
        /*
          Some DELETE responses may return no body.
        */
      }

      if (!response.ok) {
        throw new Error(
          data.message ||
            `Failed to delete student (${response.status}).`
        );
      }

      setStudents((previous) =>
        previous.filter(
          (item) =>
            item.student_id !==
            student.student_id
        )
      );

      showToast(
        `${student.name} was removed from the database.`
      );

      await fetchDashboard();
    } catch (error) {
      console.error(
        "Delete student error:",
        error
      );

      showToast(
        `Unable to delete student: ${error.message}`
      );
    } finally {
      setDeletingStudentId(null);
    }
  }

  /* =====================================================
     START CAMERA
  ===================================================== */

  const startCamera =
    useCallback(async () => {
      try {
        setCameraError("");

        if (
          !navigator.mediaDevices ||
          !navigator.mediaDevices
            .getUserMedia
        ) {
          throw new Error(
            "Camera access is not supported by this browser."
          );
        }

        /*
          Prevent opening a second stream.
        */
        if (streamRef.current) {
          return true;
        }

        const stream =
          await navigator.mediaDevices.getUserMedia(
            {
              video: {
                width: {
                  ideal: 1280,
                },
                height: {
                  ideal: 720,
                },
                facingMode: "user",
              },
              audio: false,
            }
          );

        streamRef.current = stream;

        /*
          Attach immediately if video is already
          rendered.
        */
        if (videoRef.current) {
          videoRef.current.srcObject =
            stream;

          await videoRef.current.play();
        }

        return true;
      } catch (error) {
        console.error(
          "CAMERA ERROR:",
          error
        );

        setCameraError(
          error.message ||
            "Unable to access camera."
        );

        return false;
      }
    }, []);

  /* =====================================================
     ATTACH EXISTING CAMERA TO VIDEO
     
     IMPORTANT:
     If the user starts the session on Dashboard
     and then navigates to Live Attendance, the
     video element gets mounted later.

     This effect attaches the already-running
     stream to that new video element.
  ===================================================== */

  useEffect(() => {
    if (
      sessionActive &&
      videoRef.current &&
      streamRef.current
    ) {
      videoRef.current.srcObject =
        streamRef.current;

      videoRef.current
        .play()
        .catch(() => {});
    }
  }, [
    activeNav,
    sessionActive,
  ]);

  /* =====================================================
     STOP CAMERA
  ===================================================== */

  const stopCamera =
    useCallback(() => {
      if (streamRef.current) {
        streamRef.current
          .getTracks()
          .forEach((track) =>
            track.stop()
          );

        streamRef.current = null;
      }

      if (videoRef.current) {
        videoRef.current.srcObject =
          null;
      }
    }, []);

  /* =====================================================
     RECOGNIZE CURRENT CAMERA FRAME

     NOTE:
     The backend now returns a MULTI-FACE shape:

       {
         success, ready, face_count, minimum_faces,
         matched_count, marked_count, already_marked_count,
         unknown_count, spoof_count, message,
         faces: [
           {
             face_index, status, is_real, antispoof_score,
             matched, student: { student_id, usn, name },
             distance, confidence
           },
           ...
         ]
       }

     There is NO top-level "matched" / "student" / "distance"
     field anymore — those live inside each entry of
     "faces". This block reads the new shape directly.
  ===================================================== */

  const recognizeCurrentFrame =
    useCallback(async () => {
      if (
        !sessionId ||
        !sessionActive ||
        recognitionBusyRef.current
      ) {
        return;
      }

      const video =
        videoRef.current;

      if (
        !video ||
        video.readyState <
          HTMLMediaElement.HAVE_CURRENT_DATA ||
        video.videoWidth === 0 ||
        video.videoHeight === 0
      ) {
        return;
      }

      recognitionBusyRef.current =
        true;

      setRecognitionLoading(true);

      try {
        const canvas =
          document.createElement("canvas");

        /*
          Reduce image size before sending
          to Flask/DeepFace.
        */
        const maxWidth = 960;

        const scale = Math.min(
          1,
          maxWidth / video.videoWidth
        );

        canvas.width = Math.round(
          video.videoWidth * scale
        );

        canvas.height = Math.round(
          video.videoHeight * scale
        );

        const context =
          canvas.getContext("2d");

        /*
          Capture normal camera image.
          The preview itself is mirrored only
          for the user's viewing experience.
        */
        context.drawImage(
          video,
          0,
          0,
          canvas.width,
          canvas.height
        );

        const blob =
          await new Promise(
            (resolve) => {
              canvas.toBlob(
                resolve,
                "image/jpeg",
                0.82
              );
            }
          );

        if (!blob) {
          throw new Error(
            "Could not capture camera frame."
          );
        }

        const formData =
          new FormData();

        formData.append(
          "session_id",
          String(sessionId)
        );

        formData.append(
          "image",
          blob,
          "camera.jpg"
        );

        const response =
          await fetch(
            `${API_BASE_URL}/api/attendance/recognize`,
            {
              method: "POST",
              body: formData,
            }
          );

        const data =
          await response.json();

        console.log(
          "RECOGNITION RESULT:",
          data
        );

        if (!response.ok) {
          throw new Error(
            data.message ||
              `Recognition failed (${response.status})`
          );
        }

        const now = new Date();

        const currentTime =
          now.toLocaleTimeString(
            "en-IN",
            {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            }
          );

        /* =========================================
           MINIMUM FACES NOT REACHED

           Backend returns ready:false and an empty
           faces[] when fewer than minimum_faces are
           in view. Nothing was recognized at all.
        ========================================= */

        if (!data.ready) {
          setRecognitionResult({
            type: "unknown",
            name: "Unknown face",
            usn: "—",
            confidence: null,
            distance: null,
            time: currentTime,
            alreadyMarked: false,
            message:
              data.message ||
              `Need at least ${
                data.minimum_faces ?? 3
              } faces in frame.`,
          });

          return;
        }

        /* =========================================
           PICK THE FIRST USEFUL FACE

           Prefer a matched face if there are
           multiple detected faces; otherwise fall
           back to the first face's result.
        ========================================= */

        const faces = Array.isArray(data.faces)
          ? data.faces
          : [];

        const matchedFace = faces.find(
          (face) =>
            face.matched &&
            face.student
        );

        const face = matchedFace || faces[0];

        /* =========================================
           MATCHED (newly marked or already marked)
        ========================================= */

        if (
          face &&
          face.matched &&
          face.student
        ) {
          const distance =
            Number(face.distance);

          const confidence =
            face.confidence !== undefined &&
            face.confidence !== null
              ? Number(face.confidence)
              : Number.isFinite(distance)
              ? Math.max(
                  0,
                  Math.min(
                    100,
                    (1 - distance) * 100
                  )
                )
              : null;

          const alreadyMarked =
            face.status === "ALREADY_MARKED";

          setRecognitionResult({
            type: "matched",
            name:
              face.student.name,
            usn:
              face.student.usn,
            confidence,
            distance,
            time: currentTime,
            alreadyMarked,
            message:
              alreadyMarked
                ? "Attendance already marked for this session."
                : "Attendance marked successfully.",
          });

          if (!alreadyMarked) {
            showToast(
              `${face.student.name} — attendance marked`
            );

            /*
              Refresh attendance after a successful
              new attendance record.
            */
            fetchAttendance();
            fetchDashboard();
          }
        }

        /* =========================================
           SPOOF FACE
        ========================================= */

        else if (
          face &&
          face.status === "SPOOF"
        ) {
          setRecognitionResult({
            type: "unknown",
            name: "Spoof detected",
            usn: "—",
            confidence: null,
            distance: null,
            time: currentTime,
            alreadyMarked: false,
            message:
              "Possible spoof attempt — attendance not marked.",
          });
        }

        /* =========================================
           UNKNOWN (real face, no match) or nothing
           returned at all
        ========================================= */

        else {
          setRecognitionResult({
            type: "unknown",
            name: "Unknown face",
            usn: "—",
            confidence: null,
            distance:
              face?.distance ?? null,
            time: currentTime,
            alreadyMarked: false,
            message:
              "Face not recognized.",
          });
        }
      } catch (error) {
        console.error(
          "RECOGNITION ERROR:",
          error
        );

        setRecognitionResult({
          type: "error",
          name: "Recognition error",
          usn: "—",
          confidence: null,
          distance: null,
          time: "",
          message:
            error.message ||
            "Recognition request failed.",
        });
      } finally {
        recognitionBusyRef.current =
          false;

        setRecognitionLoading(false);
      }
    }, [
      sessionId,
      sessionActive,
      fetchAttendance,
      fetchDashboard,
    ]);

  /* =====================================================
     START CAMERA WHEN SESSION BECOMES ACTIVE
  ===================================================== */

  useEffect(() => {
    if (!sessionActive) {
      stopCamera();
      return;
    }

    startCamera();
  }, [
    sessionActive,
    startCamera,
    stopCamera,
  ]);

  /* =====================================================
     RECOGNITION LOOP
  ===================================================== */

  useEffect(() => {
    if (
      !sessionActive ||
      !sessionId
    ) {
      if (
        recognitionTimerRef.current
      ) {
        clearInterval(
          recognitionTimerRef.current
        );

        recognitionTimerRef.current =
          null;
      }

      return;
    }

    if (
      recognitionTimerRef.current
    ) {
      clearInterval(
        recognitionTimerRef.current
      );

      recognitionTimerRef.current =
        null;
    }

    /*
      Give the camera time to initialize.
    */
    const initialTimeout =
      setTimeout(() => {
        recognizeCurrentFrame();

        recognitionTimerRef.current =
          setInterval(() => {
            recognizeCurrentFrame();
          }, RECOGNITION_INTERVAL);
      }, 1800);

    return () => {
      clearTimeout(
        initialTimeout
      );

      if (
        recognitionTimerRef.current
      ) {
        clearInterval(
          recognitionTimerRef.current
        );

        recognitionTimerRef.current =
          null;
      }
    };
  }, [
    sessionActive,
    sessionId,
    recognizeCurrentFrame,
  ]);

  /* =====================================================
     START SESSION
  ===================================================== */

  async function startSession() {
    try {
      setRecognitionResult(null);
      setCameraError("");

      const response =
        await fetch(
          `${API_BASE_URL}/api/sessions/start`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              classroom_id:
                DEFAULT_CLASSROOM_ID,

              period_number:
                DEFAULT_PERIOD_NUMBER,
            }),
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.message ||
            "Failed to start session."
        );
      }

      console.log(
        "SESSION STARTED:",
        data
      );

      const newSessionId =
        data.session.session_id;

      setSessionId(newSessionId);
      setSessionActive(true);

      showToast(
        "Live attendance session started."
      );
    } catch (error) {
      console.error(
        "SESSION START ERROR:",
        error
      );

      showToast(
        `Unable to start session: ${error.message}`
      );
    }
  }

  /* =====================================================
     STOP SESSION
  ===================================================== */

  async function stopSession() {
    try {
      if (
        recognitionTimerRef.current
      ) {
        clearInterval(
          recognitionTimerRef.current
        );

        recognitionTimerRef.current =
          null;
      }

      stopCamera();

      if (sessionId) {
        const response =
          await fetch(
            `${API_BASE_URL}/api/sessions/${sessionId}/stop`,
            {
              method: "POST",
            }
          );

        const data =
          await response.json();

        console.log(
          "SESSION STOPPED:",
          data
        );
      }

      setSessionActive(false);
      setSessionId(null);
      setRecognitionResult(null);
      setRecognitionLoading(false);

      await fetchDashboard();
      await fetchAttendance();

      showToast(
        "Session stopped."
      );
    } catch (error) {
      console.error(
        "SESSION STOP ERROR:",
        error
      );

      /*
        Even if backend stopping fails,
        terminate the local session.
      */
      setSessionActive(false);
      setSessionId(null);

      stopCamera();

      showToast(
        "Session stopped locally, but backend stop request failed."
      );
    }
  }

  /* =====================================================
     CLEANUP WHEN APP UNMOUNTS
  ===================================================== */

  useEffect(() => {
    return () => {
      if (
        recognitionTimerRef.current
      ) {
        clearInterval(
          recognitionTimerRef.current
        );
      }

      if (streamRef.current) {
        streamRef.current
          .getTracks()
          .forEach((track) =>
            track.stop()
          );
      }
    };
  }, []);

  /* =====================================================
     PAGE META
  ===================================================== */

  const meta =
    PAGE_META[activeNav];

  /* =====================================================
     RENDER
  ===================================================== */

  return (
    <div className="sa-app">
      {/* MOBILE BACKDROP */}

      <div
        className={`sa-mobile-backdrop ${
          mobileNavOpen ? "open" : ""
        }`}
        onClick={() =>
          setMobileNavOpen(false)
        }
      />

      {/* SIDEBAR */}

      <aside
        className={`sa-sidebar ${
          mobileNavOpen ? "open" : ""
        }`}
      >
        <div className="sa-sidebar-brand">
          <div className="sa-brand-mark">
            <ScanFace
              size={16}
              color="#fff"
            />
          </div>

          <span className="sa-brand-name">
            Smart Attendance
          </span>
        </div>

        <nav className="sa-nav">
          <div className="sa-nav-group-label">
            Main
          </div>

          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.id}
                className={`sa-nav-item ${
                  activeNav === item.id
                    ? "active"
                    : ""
                }`}
                onClick={() =>
                  go(item.id)
                }
              >
                <Icon size={16} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="sa-sidebar-footer">
          <button className="sa-nav-item">
            <Settings size={16} />
            Settings
          </button>

          <button className="sa-nav-item">
            <UserCircle2 size={16} />
            Faculty profile
          </button>
        </div>
      </aside>

      {/* MAIN COLUMN */}

      <div className="sa-main-col">
        {/* HEADER */}

        <header className="sa-header">
          <div className="sa-header-left">
            <button
              className="sa-menu-btn"
              onClick={() =>
                setMobileNavOpen(
                  (value) => !value
                )
              }
              aria-label="Toggle menu"
            >
              <Menu size={16} />
            </button>

            <div className="sa-header-titles">
              <span className="sa-header-title">
                Smart Attendance
              </span>

              <span className="sa-header-subtitle">
                AI-Powered Attendance
                Management
              </span>
            </div>
          </div>

          <div className="sa-header-right">
            <span className="sa-status-pill">
              <span className="sa-status-dot" />
              System online
            </span>

            <button className="sa-profile">
              <div className="sa-avatar">
                AR
              </div>

              <div className="sa-profile-meta">
                <span className="sa-profile-name">
                  Prof. Ananya Rao
                </span>

                <span className="sa-profile-role">
                  Faculty
                </span>
              </div>

              <ChevronDown
                size={14}
                color="var(--text-tertiary)"
              />
            </button>
          </div>
        </header>

        {/* MAIN */}

        <main className="sa-main">
          <div className="sa-page-head">
            <p className="sa-page-title">
              {meta.title}
            </p>

            <p className="sa-page-subtitle">
              {meta.sub}
            </p>
          </div>

          {/* DASHBOARD */}

          {activeNav === "dashboard" && (
            <DashboardView
              students={students}
              studentsLoading={
                studentsLoading
              }
              sessionActive={
                sessionActive
              }
              sessionId={sessionId}
              onStart={startSession}
              onStop={stopSession}
              onAddStudent={() =>
                setModalOpen(true)
              }
              onViewStudents={() =>
                go("students")
              }
              onRefreshStudents={
                fetchStudents
              }
              recognitionResult={
                recognitionResult
              }
              recognitionLoading={
                recognitionLoading
              }
              cameraError={cameraError}
              videoRef={videoRef}
              dashboardData={
                dashboardData
              }
              attendance={attendance}
            />
          )}

          {/* LIVE */}

          {activeNav === "live" && (
            <LiveAttendanceSection
              sessionActive={
                sessionActive
              }
              sessionId={sessionId}
              onStart={startSession}
              onStop={stopSession}
              recognitionResult={
                recognitionResult
              }
              recognitionLoading={
                recognitionLoading
              }
              cameraError={cameraError}
              videoRef={videoRef}
            />
          )}

          {/* STUDENTS */}

          {activeNav === "students" && (
            <StudentsView
              students={students}
              loading={
                studentsLoading
              }
              error={studentsError}
              onAddStudent={() =>
                setModalOpen(true)
              }
              onRefresh={
                fetchStudents
              }
              onDeleteStudent={
                handleDeleteStudent
              }
              deletingId={
                deletingStudentId
              }
            />
          )}

          {/* ATTENDANCE */}

          {activeNav === "attendance" && (
            <AttendanceView
              attendance={attendance}
              loading={
                attendanceLoading
              }
              error={
                attendanceError
              }
              onRefresh={
                fetchAttendance
              }
            />
          )}

         {/* OTHER PAGES */}

{[
  'attendance',
  'classrooms',
  'sessions'
].includes(activeNav) && (

  <EmptyView
    nav={activeNav}
  />

)}


{/* REPORTS */}

{activeNav === 'reports' && (

  <ReportsView />

)}
        </main>
      </div>

      {/* ADD STUDENT MODAL */}

      {modalOpen && (
        <AddStudentModal
          onClose={() =>
            setModalOpen(false)
          }
          onSubmit={handleEnroll}
        />
      )}

      {/* TOAST */}

      {toast && (
        <div className="sa-toast">
          <CheckCircle2
            size={16}
            className="sa-toast-icon"
          />

          {toast}
        </div>
      )}
    </div>
  );
}