import type { ButtonHTMLAttributes } from "react";

interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean;
}

export function Chip({ selected, className, ...rest }: ChipProps) {
  const classes = ["chip", selected ? "selected" : "", className ?? ""]
    .filter(Boolean)
    .join(" ");
  return <button type="button" className={classes} {...rest} />;
}
