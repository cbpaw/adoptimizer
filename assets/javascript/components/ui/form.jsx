import * as React from "react"
import { cn } from "@/utilities/shadcn"

function Form({ className, ...props }) {
  return (
    <form
      className={cn("space-y-6", className)}
      {...props}
    />
  )
}

function FormField({ className, ...props }) {
  return (
    <div
      className={cn("space-y-2", className)}
      {...props}
    />
  )
}

function FormLabel({ className, ...props }) {
  return (
    <label
      className={cn(
        "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
        className
      )}
      {...props}
    />
  )
}

function FormDescription({ className, ...props }) {
  return (
    <p
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  )
}

function FormMessage({ className, ...props }) {
  return (
    <p
      className={cn("text-sm font-medium text-destructive", className)}
      {...props}
    />
  )
}

export { Form, FormField, FormLabel, FormDescription, FormMessage }