import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-gradient-primary text-white hover:shadow-lg hover:shadow-accent-orange/30 hover:-translate-y-0.5",
        gradient: "bg-gradient-primary text-white hover:bg-gradient-secondary hover:shadow-lg hover:shadow-accent-orange/30 hover:-translate-y-0.5",
        "gradient-warm": "bg-gradient-warm text-white hover:shadow-lg hover:shadow-accent-yellow/30 hover:-translate-y-0.5",
        destructive: "bg-accent-red text-white hover:bg-accent-red/90",
        outline: "border border-accent-orange/50 bg-transparent hover:bg-gradient-primary hover:text-white hover:border-accent-orange",
        secondary: "bg-dark-surface text-white hover:bg-dark-surface/80",
        ghost: "text-gray-300 hover:bg-gradient-primary/10 hover:text-accent-orange",
        link: "text-accent-orange underline-offset-4 hover:underline hover:text-accent-orange-light",
        success: "bg-accent-green text-white hover:bg-accent-green/90",
        warning: "bg-gradient-secondary text-gray-900 font-semibold hover:shadow-lg hover:shadow-accent-yellow/30 hover:-translate-y-0.5",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {children}
      </Comp>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
