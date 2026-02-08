import { useEffect, useState } from "react";
import { MeetingCard } from "@/components/MeetingCard";
import { useProject } from "@/contexts/ProjectContext";
import { fetchMeetings, reviewMeeting, type Meeting } from "@/data/meetings";
import { Calendar } from "lucide-react";
import { toast } from "sonner";

export default function Meetings() {
  const { selectedProject } = useProject();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [submittingMeetingId, setSubmittingMeetingId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);

    fetchMeetings(selectedProject.project_id)
      .then((response) => {
        if (!active) {
          return;
        }
        setMeetings(response.meetings ?? []);
      })
      .catch((error) => {
        console.error("Error loading meetings:", error);
        if (active) {
          setMeetings([]);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedProject.project_id]);

  const handleReview = async (meetingId: string, action: "approve" | "deny") => {
    setSubmittingMeetingId(meetingId);
    try {
      const response = await reviewMeeting(selectedProject.project_id, meetingId, action);
      setMeetings((current) =>
        current.map((meeting) =>
          meeting.meeting_id === meetingId
            ? { ...meeting, status: response.status, locked: response.locked }
            : meeting
        )
      );
      toast.success(response.message);
    } catch (error) {
      console.error("Error reviewing meeting:", error);
      toast.error("Failed to update meeting review status.");
    } finally {
      setSubmittingMeetingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="relative">
        <div className="flex items-center gap-4 mb-2">
          <div className="relative">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/30">
              <Calendar className="h-5 w-5 text-white" />
            </div>
            <div className="absolute inset-0 blur-lg bg-cyan-400/30" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-blue-100">
            Meetings
          </h1>
        </div>
        <p className="mt-1 text-blue-300/70">
          Recent meetings and the decisions extracted from{" "}
          <span className="font-medium text-cyan-300">
            {selectedProject.project_name}
          </span>
        </p>
      </div>

      {/* Meetings Grid */}
      {meetings.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {meetings.map((meeting) => (
            <MeetingCard
              key={meeting.meeting_id}
              meeting={meeting}
              onReview={(action) => handleReview(meeting.meeting_id, action)}
              isSubmitting={submittingMeetingId === meeting.meeting_id}
            />
          ))}
        </div>
      ) : (
        <div className="relative">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-2xl blur" />
          <div className="relative rounded-xl border border-blue-500/30 bg-[#0d1225] p-8 text-center backdrop-blur-sm">
            <p className="text-sm text-blue-300/70">
              {loading ? "Loading meetings..." : "No meetings found for this project."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
