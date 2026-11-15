import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";

export const introSchema = z.object({
  title: z.string(),
  subtitle: z.string(),
  accent: z.string(),
});

export const Intro: React.FC<z.infer<typeof introSchema>> = ({
  title,
  subtitle,
  accent,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const titleIn = spring({ frame, fps, config: { damping: 200 } });
  const subtitleIn = spring({ frame: frame - 20, fps, config: { damping: 200 } });
  const barWidth = interpolate(frame, [10, 50], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0f0f14",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "Helvetica, Arial, sans-serif",
        opacity: fadeOut,
      }}
    >
      <div style={{ textAlign: "center" }}>
        <h1
          style={{
            color: "white",
            fontSize: 140,
            fontWeight: 800,
            margin: 0,
            opacity: titleIn,
            transform: `translateY(${interpolate(titleIn, [0, 1], [60, 0])}px)`,
          }}
        >
          {title}
        </h1>
        <div
          style={{
            height: 10,
            width: `${barWidth}%`,
            backgroundColor: accent,
            borderRadius: 5,
            margin: "24px auto",
          }}
        />
        <p
          style={{
            color: "#b8b8c8",
            fontSize: 56,
            margin: 0,
            opacity: subtitleIn,
            transform: `translateY(${interpolate(subtitleIn, [0, 1], [30, 0])}px)`,
          }}
        >
          {subtitle}
        </p>
      </div>
    </AbsoluteFill>
  );
};
