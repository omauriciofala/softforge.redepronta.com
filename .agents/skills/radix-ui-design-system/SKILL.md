---
name: radix-ui-design-system
description: "Padrão de UI do SoftForge: componentes headless acessíveis com Radix UI, estilização composível com Tailwind CSS + CVA, e suporte ao sistema de temas dinâmicos (White-Labeling)."
risk: safe
source: community-adapted-softforge
date_added: "2026-10-11"
---

# Radix UI & Design System Patterns (SoftForge)

Guia de desenvolvimento de componentes de interface para o SoftForge em `apps/web/src/components/ui/`, combinando **Radix UI Primitives + Tailwind CSS + Class Variance Authority (CVA) + CSS Variables**.

---

## 1. Princípios Inegociáveis

1. **Acessibilidade Embutida (WAI-ARIA):** Todo componente interativo complexo (modais, menus, dropdowns, tabs, tooltips) deve ser baseado em um primitivo do `@radix-ui`. Nunca implemente controle de foco ou listeners de teclado na mão quando houver primitivo Radix.
2. **Separação de Comportamento e Aparência:** O Radix governa o comportamento e a acessibilidade (*headless*). O Tailwind CSS e o CVA governam o estilo e as variantes visuais.
3. **Respeito aos Tokens de Tema (White-Labeling):** NUNCA use cores literais fixas (ex: `bg-blue-600` ou `text-red-500`). Use sempre as classes semânticas mapeadas nas variáveis CSS de `index.css`:
   - `bg-primary text-primary-foreground`
   - `bg-secondary text-secondary-foreground`
   - `bg-destructive text-destructive-foreground`
   - `bg-muted text-muted-foreground`
   - `border-border`, `border-input`, `ring-ring`

---

## 2. Anatomia Padrão de um Componente UI (`components/ui/`)

Todo novo componente em `apps/web/src/components/ui/` deve seguir esta estrutura:

```tsx
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

// 1. Variantes CVA com classes Tailwind semânticas
const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

// 2. Interface tipada estendendo atributos HTML e variantes
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

// 3. Componente com forwardRef e suporte a polimorfismo via Radix Slot
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
```

---

## 3. Implementando Diálogos e Modais com Radix UI

Ao criar modais ou diálogos (ex: confirmações de exclusão, edição de tarefas de dev ou convite de membros), encapsule os primitivos do `@radix-ui/react-dialog`:

```tsx
import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPrimitive.Portal>
    {/* Overlay escuro com animação suave */}
    <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
    {/* Conteúdo centralizado com foco automático */}
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 sm:rounded-lg",
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
        <X className="h-4 w-4" />
        <span className="sr-only">Fechar</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;
```

---

## 4. Integração com o White-Labeling (`workspace_themes`)

O SoftForge permite que cada workspace personalize cores e logos (`themes` slice).
- Para suportar isso, o tema injeta valores HSL em `--primary`, `--primary-foreground`, etc., no contêiner da página.
- Ao usar classes como `bg-primary`, qualquer alteração de tema feita pelo usuário no banco é refletida instantaneamente sem reescrever o CSS do componente.

---

## 5. Checklist de Qualidade de Componentes UI

- [ ] O componente aceita `className` e mescla estilos via `cn(...)`?
- [ ] O componente expõe `ref` através de `React.forwardRef`?
- [ ] Nenhum estilo utiliza cores literais arbitrárias (somente tokens semânticos)?
- [ ] Componentes com ícones interativos incluem texto acessível oculto (`<span className="sr-only">...</span>`)?
- [ ] O typecheck do frontend passa com sucesso (`npm run typecheck`)?
