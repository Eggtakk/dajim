export function Icon({
  name,
  className,
  style,
}: {
  name: string;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <svg className={className ? `icon ${className}` : "icon"} style={style}>
      <use href={`#${name}`} />
    </svg>
  );
}
