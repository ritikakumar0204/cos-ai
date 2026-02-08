import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Volume2, Play, Pause, Mail, MessageSquare, Calendar, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { synthesizeSpeech, transcribeSpeech } from "@/data/tts";

export type CommunicationChannel = "voice" | "email" | "slack" | "calendar";

export interface SuggestedCommunication {
  channel: CommunicationChannel;
  recipient: string;
  preview: string;
}

export interface AIBriefingPanelProps {
  summary: string;
  suggestedCommunications?: SuggestedCommunication[];
  className?: string;
  onRecordedMessage?: (message: string) => Promise<void> | void;
}

interface ChannelOption {
  id: CommunicationChannel;
  label: string;
  description: string;
  suitability: string;
  icon: typeof Mail;
  color: string;
  bgColor: string;
  borderColor: string;
}

const channelOptions: ChannelOption[] = [
  {
    id: "voice",
    label: "Voice Briefing",
    description: "Spoken summary for quick consumption",
    suitability: "Best for Leads & Managers",
    icon: Mic,
    color: "text-primary",
    bgColor: "bg-primary/10",
    borderColor: "border-primary/20",
  },
  {
    id: "email",
    label: "Email Summary",
    description: "Detailed context with documentation",
    suitability: "Best for Owners & Contributors",
    icon: Mail,
    color: "text-blue-600 dark:text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20",
  },
  {
    id: "slack",
    label: "Slack Update",
    description: "Quick notification for fast acknowledgment",
    suitability: "Best for Informed & Affected",
    icon: MessageSquare,
    color: "text-purple-600 dark:text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/20",
  },
  {
    id: "calendar",
    label: "Calendar Context",
    description: "Meeting history and scheduling reference",
    suitability: "Read-only • For context",
    icon: Calendar,
    color: "text-emerald-600 dark:text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20",
  },
];

const channelConfigMap: Record<CommunicationChannel, { icon: typeof Mail; label: string; color: string }> = {
  voice: {
    icon: Mic,
    label: "Voice",
    color: "text-primary",
  },
  email: {
    icon: Mail,
    label: "Email",
    color: "text-blue-600 dark:text-blue-400",
  },
  slack: {
    icon: MessageSquare,
    label: "Slack",
    color: "text-purple-600 dark:text-purple-400",
  },
  calendar: {
    icon: Calendar,
    label: "Calendar",
    color: "text-emerald-600 dark:text-emerald-400",
  },
};

export function AIBriefingPanel({ 
  summary, 
  suggestedCommunications = [],
  className,
  onRecordedMessage,
}: AIBriefingPanelProps) {
  const fallbackSummary =
    "Maya Chen (Lead) in Product is referencing an earlier version of this decision. A targeted update would bring Product into alignment and prevent execution inconsistencies.";
  const effectiveSummary = summary.trim() ? summary : fallbackSummary;

  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [recordedTranscript, setRecordedTranscript] = useState<string>("");
  const [selectedChannel, setSelectedChannel] = useState<CommunicationChannel | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        recorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, [audioUrl]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setIsPlaying(false);
  }, [summary]);

  const playFromBlob = async (blob: Blob) => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }

    const nextUrl = URL.createObjectURL(blob);
    setAudioUrl(nextUrl);

    const audio = new Audio(nextUrl);
    audio.preload = "auto";
    audio.muted = false;
    audio.volume = 1;
    audioRef.current = audio;
    audio.onended = () => setIsPlaying(false);
    audio.onpause = () => setIsPlaying(false);

    await audio.play();
    setIsPlaying(true);
  };

  const handlePlayToggle = async () => {
    if (isLoadingAudio) {
      return;
    }

    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      return;
    }

    if (audioRef.current) {
      try {
        await audioRef.current.play();
        setIsPlaying(true);
      } catch (playbackError) {
        if (playbackError instanceof DOMException && playbackError.name === "NotAllowedError") {
          toast.error("Playback was blocked by the browser. Click play again after interacting with the page.");
        } else {
          console.error("Voice playback resume failed:", playbackError);
          toast.error("Audio playback failed in the browser.");
        }
      }
      return;
    }

    try {
      setIsLoadingAudio(true);
      const audioBlob = await synthesizeSpeech(effectiveSummary);

      try {
        await playFromBlob(audioBlob);
      } catch (playbackError) {
        if (playbackError instanceof DOMException && playbackError.name === "AbortError") {
          // Ignore aborted playback (for example, rapid toggles).
        } else if (playbackError instanceof DOMException && playbackError.name === "NotAllowedError") {
          toast.error("Playback was blocked by the browser. Click play again after interacting with the page.");
        } else {
          console.error("Voice playback failed:", playbackError);
          toast.error("Audio playback failed in the browser.");
        }

        setIsPlaying(false);
      }
    } catch (error) {
      console.error("Voice request failed:", error);
      toast.error("Voice generation failed. Check backend/ElevenLabs response.");
      setIsPlaying(false);
    } finally {
      setIsLoadingAudio(false);
    }
  };

  const handleRecordToggle = async () => {
    if (isTranscribing) {
      return;
    }

    if (isRecording) {
      recorderRef.current?.stop();
      setIsRecording(false);
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      toast.error("Audio recording is not supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      streamRef.current = stream;
      recorderRef.current = recorder;
      recordedChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const mimeType = recorder.mimeType || "audio/webm";
        const audioBlob = new Blob(recordedChunksRef.current, { type: mimeType });
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;

        if (audioBlob.size === 0) {
          toast.error("No audio was captured. Please try recording again.");
          return;
        }

        try {
          setIsTranscribing(true);
          const transcript = await transcribeSpeech(audioBlob);
          setRecordedTranscript(transcript);
          toast.success("Recording transcribed successfully.");

          if (onRecordedMessage) {
            await onRecordedMessage(transcript);
          }
        } catch (error) {
          console.error("Voice transcription failed:", error);
          toast.error("Could not transcribe the recording.");
        } finally {
          setIsTranscribing(false);
        }
      };

      recorder.start();
      setIsRecording(true);
      toast.success("Recording started.");
    } catch (error) {
      console.error("Audio recording failed:", error);
      toast.error("Microphone permission denied or unavailable.");
      setIsRecording(false);
    }
  };

  return (
    <Card className={cn("border-border bg-card", className)}>
      <CardContent className="p-5 space-y-5">
        {/* Header */}
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10">
            <span className="text-xs font-semibold text-primary">AI</span>
          </div>
          <h3 className="text-sm font-medium text-foreground">Briefing</h3>
        </div>

        {/* Summary Text with Voice Control */}
        <div className="rounded-lg border border-border bg-muted/30 overflow-hidden">
          {/* Voice Playback Control */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-border/60 bg-muted/20">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePlayToggle}
              disabled={isLoadingAudio}
              className={cn(
                "h-9 w-9 p-0 rounded-full border-2 transition-all",
                isPlaying 
                  ? "border-primary bg-primary/10 text-primary" 
                  : "border-muted-foreground/30 hover:border-primary/50 hover:bg-primary/5"
              )}
            >
              {isPlaying ? (
                <Pause className="h-4 w-4" />
              ) : (
                <Play className="h-4 w-4 ml-0.5" />
              )}
            </Button>
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground">
                {isLoadingAudio
                  ? "Generating voice summary..."
                  : isPlaying
                  ? "Playing voice summary..."
                  : "Play voice summary"}
              </p>
              <p className="text-xs text-muted-foreground">
                {isLoadingAudio ? "Contacting ElevenLabs" : isPlaying ? "Tap to pause" : "Listen to this briefing"}
              </p>
            </div>
            {selectedChannel === "voice" && onRecordedMessage && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleRecordToggle}
                disabled={isTranscribing}
                className={cn(
                  "h-9 rounded-full border-2 px-3 transition-all",
                  isRecording
                    ? "border-red-500 bg-red-500/10 text-red-600"
                    : "border-muted-foreground/30 hover:border-primary/50 hover:bg-primary/5"
                )}
              >
                <Mic className="mr-1.5 h-4 w-4" />
                {isRecording ? "Stop" : isTranscribing ? "Transcribing..." : "Record"}
              </Button>
            )}
            <Volume2 className={cn(
              "h-4 w-4 transition-colors",
              isPlaying ? "text-primary" : "text-muted-foreground/50"
            )} />
          </div>

          {/* Summary Text */}
          <div className="px-4 py-3">
            <p className="text-sm leading-relaxed text-foreground">
              {effectiveSummary}
            </p>
          </div>

          {audioUrl && (
            <div className="px-4 pb-3">
              <audio controls src={audioUrl} className="w-full" />
              <p className="mt-1 text-[11px] text-muted-foreground">
                If auto-play is blocked, use this player to test the generated audio.
              </p>
            </div>
          )}

          {recordedTranscript && (
            <div className="px-4 pb-3">
              <div className="rounded-md border border-border/60 bg-muted/20 p-3">
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">
                  Recorded Transcript
                </p>
                <p className="mt-1 text-sm text-foreground">{recordedTranscript}</p>
              </div>
            </div>
          )}
        </div>

        {/* Communication Channels */}
        <div className="space-y-3">
          <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Communication Channels
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {channelOptions.map((channel) => {
              const ChannelIcon = channel.icon;
              const isCalendar = channel.id === "calendar";
              
              return (
                <button
                  key={channel.id}
                  onClick={() => {
                    setSelectedChannel(channel.id);
                    if (isCalendar) {
                      navigate("/meetings");
                    } else {
                      toast.success(`${channel.label} channel selected`);
                    }
                  }}
                  className={cn(
                    "rounded-lg border p-3 transition-all text-left cursor-pointer",
                    channel.borderColor,
                    "hover:scale-[1.02] hover:shadow-md hover:border-opacity-60 active:scale-[0.98]",
                    selectedChannel === channel.id && "ring-2 ring-primary/40 border-primary/40"
                  )}
                >
                  <div className="flex items-start gap-2.5">
                    <div className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-md shrink-0",
                      channel.bgColor
                    )}>
                      <ChannelIcon className={cn("h-4 w-4", channel.color)} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-foreground leading-tight">
                        {channel.label}
                      </p>
                      <p className="text-[11px] text-muted-foreground mt-0.5 leading-snug">
                        {channel.description}
                      </p>
                      <p className={cn(
                        "text-[10px] font-medium mt-1.5",
                        channel.color
                      )}>
                        {channel.suitability}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Suggested Communications */}
        {suggestedCommunications.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Suggested Messages
            </h4>
            <div className="space-y-2">
              {suggestedCommunications.map((comm, index) => {
                const config = channelConfigMap[comm.channel];
                const ChannelIcon = config.icon;
                
                return (
                  <div
                    key={index}
                    className="flex items-start gap-3 rounded-md border border-border/60 bg-card px-3 py-2.5"
                  >
                    {/* Channel Icon */}
                    <div className={cn("mt-0.5", config.color)}>
                      <ChannelIcon className="h-4 w-4" />
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-medium text-foreground">
                          {config.label}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          → {comm.recipient}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                        "{comm.preview}"
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
            
            {/* Disclaimer */}
            <p className="text-[10px] text-muted-foreground/60 italic">
              Preview only — no messages will be sent
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
