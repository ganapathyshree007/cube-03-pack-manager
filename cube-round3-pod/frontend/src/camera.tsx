import { useEffect, useRef, useState } from "react";

export function CameraCapture({
  onCapture,
}: {
  onCapture: (file: File) => void;
}) {
  const [open, setOpen] = useState(false);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const video = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    let stream: MediaStream | undefined;
    setReady(false);
    setError("");
    (async () => {
      try {
        if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia)
          throw new Error(
            "Camera access requires HTTPS and a supported browser. You can still upload a photograph.",
          );
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        if (video.current) {
          video.current.srcObject = stream;
          await video.current.play();
          if (!cancelled) setReady(true);
        }
      } catch {
        if (!cancelled)
          setError(
            "Camera unavailable or permission declined. Close the camera and use Choose photograph.",
          );
      }
    })();
    return () => {
      cancelled = true;
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, [open]);
  function capture() {
    const source = video.current;
    if (!source?.videoWidth || !source.videoHeight) return;
    const canvas = document.createElement("canvas");
    const scale = Math.min(
      1,
      2048 / Math.max(source.videoWidth, source.videoHeight),
    );
    canvas.width = Math.round(source.videoWidth * scale);
    canvas.height = Math.round(source.videoHeight * scale);
    canvas
      .getContext("2d")
      ?.drawImage(source, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError("Could not capture the photograph. Use file upload.");
          return;
        }
        onCapture(
          new File([blob], "primary-camera.jpg", { type: "image/jpeg" }),
        );
        setOpen(false);
      },
      "image/jpeg",
      0.95,
    );
  }
  return (
    <div className="camera-capture">
      {!open ? (
        <button
          className="secondary"
          type="button"
          onClick={() => setOpen(true)}
        >
          Use rear camera
        </button>
      ) : (
        <section aria-label="Primary photograph camera">
          <p>
            <strong>Primary counting photograph:</strong> place every item in
            one layer, include the entire open box, expose distinguishing labels
            and avoid glare. Do not include catalogue reference pictures in the
            box.
          </p>
          <video
            ref={video}
            muted
            playsInline
            aria-label="Live primary photograph preview"
            style={{ width: "100%", maxHeight: 360 }}
          />
          {error ? (
            <p role="alert">{error}</p>
          ) : (
            !ready && (
              <p role="status">
                Waiting for camera permission. You can close this panel at any
                time.
              </p>
            )
          )}
          <button
            type="button"
            className="primary"
            disabled={!ready}
            onClick={capture}
          >
            Capture primary photograph
          </button>{" "}
          <button
            type="button"
            className="secondary"
            onClick={() => setOpen(false)}
          >
            Close camera
          </button>
        </section>
      )}
    </div>
  );
}
