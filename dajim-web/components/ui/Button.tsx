import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "ghost" | "accent";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  block?: boolean;
}

export function Button({
  variant = "primary",
  block,
  className,
  ...rest
}: ButtonProps) {
  const classes = [
    "btn",
    `btn-${variant}`,
    block ? "btn-block" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");
  return <button className={classes} {...rest} />;
}
