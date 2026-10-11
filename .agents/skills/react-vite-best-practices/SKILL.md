---
name: react-vite-best-practices
description: "Diretrizes essenciais de performance, renderização e arquitetura para aplicações React 18 SPA com Vite, TypeScript, TanStack Query e Tailwind CSS."
risk: safe
source: adapted-from-vercel-react-best-practices
date_added: "2026-10-11"
---

# React + Vite Best Practices (SoftForge)

Guia de boas práticas e otimização de performance para o frontend do SoftForge, adaptado da especificação da Vercel para o nosso ecossistema real: **Vite 5 + React 18 SPA + TypeScript + TanStack Query v5 + Tailwind CSS**.

---

## 1. Quando Utilizar Esta Skill

Consulte e aplique estas diretrizes sempre que:
- Criar ou refatorar componentes, páginas ou hooks em `apps/web/src/`.
- Integrar dados de APIs e gerenciar estados assíncronos via TanStack Query (`src/api/generated/`).
- Otimizar re-renders, tempo de carregamento e tamanho de bundle da aplicação.
- Fazer code review ou auditar performance e ergonomia no frontend.

---

## 2. Princípios Fundamentais por Prioridade

| Prioridade | Categoria | Foco | Prefixo |
|:---|:---|:---|:---|
| **P1** | **Eliminação de Waterfalls & Data Fetching** | TanStack Query v5, chamadas paralelas, cache | `fetch-` |
| **P2** | **Otimização de Re-render** | Callbacks funcionais, estado derivado, lazy init | `rerender-` |
| **P3** | **Renderização Segura & UX** | Ternários em vez de `&&`, wrappers de animação | `render-` |
| **P4** | **Bundle Size & Code Splitting (Vite)** | `React.lazy`, imports diretos, evitar barrels | `bundle-` |
| **P5** | **JavaScript & Estruturas de Dados** | `Map`/`Set` $O(1)$, early exits, imutabilidade | `js-` |

---

## 3. Regras Práticas e Exemplos

### P1: Data Fetching & Eliminação de Waterfalls (`fetch-`)

#### `fetch-parallel` — Nunca encadeie requisições independentes
- **Incorreto:** Fazer chamadas sequenciais dentro de `useEffect` ou aguardar uma query desnecessariamente para iniciar outra que não depende dela.
- **Correto:** Disparar queries em paralelo via múltiplos hooks `useQuery` ou `useQueries` do TanStack Query.
```tsx
// Correto: Ambas as requisições acontecem em paralelo sem waterfall
const { data: user } = useGetUser();
const { data: workspaces } = useListWorkspaces();
```

#### `fetch-cache-stale` — Confie no cache do TanStack Query
- **Incorreto:** Criar estados `useState` locais duplicados apenas para armazenar a resposta da API.
- **Correto:** Consumir diretamente os dados de `data` retornados pelo hook gerado pelo Orval. O TanStack Query gerencia cache, invalidação e deduplicação automática de requisições idênticas.

---

### P2: Otimização de Re-renders (`rerender-`)

#### `rerender-functional-setstate` — Use a forma funcional em callbacks
- **Incorreto:** Incluir o estado como dependência de `useCallback` apenas para atualizá-lo:
  ```tsx
  // Evitar: recria o callback a cada alteração de count
  const increment = useCallback(() => setCount(count + 1), [count]);
  ```
- **Correto:** Usar a forma funcional `setCount(prev => prev + 1)`:
  ```tsx
  // Correto: callback estável com zero dependências
  const increment = useCallback(() => setCount(prev => prev + 1), []);
  ```

#### `rerender-derived-state` — Calcule dados derivados inline ou via `useMemo`
- **Incorreto:** Manter estado separado e sincronizá-lo via `useEffect`:
  ```tsx
  // Evitar: gera dois ciclos de renderização
  const [items, setItems] = useState<Item[]>([]);
  const [activeItems, setActiveItems] = useState<Item[]>([]);
  useEffect(() => {
    setActiveItems(items.filter(i => i.active));
  }, [items]);
  ```
- **Correto:** Calcular inline ou usar `useMemo` se o cálculo for pesado:
  ```tsx
  // Correto: derivado diretamente durante o render
  const activeItems = useMemo(() => items.filter(i => i.active), [items]);
  ```

#### `rerender-lazy-state-init` — Inicialização preguiçosa de estado caro
- **Incorreto:** Executar parsing ou leitura pesada a cada render:
  ```tsx
  // Evitar: localStorage.getItem é executado em todo ciclo de render
  const [theme, setTheme] = useState(localStorage.getItem('sf_theme') ?? 'dark');
  ```
- **Correto:** Passar uma função para inicializar o `useState`:
  ```tsx
  // Correto: executado apenas na montagem inicial
  const [theme, setTheme] = useState(() => localStorage.getItem('sf_theme') ?? 'dark');
  ```

#### `rerender-primitive-deps` — Use identificadores primitivos em dependências
- **Incorreto:** Passar objetos inteiros no array de dependências de hooks:
  ```tsx
  useEffect(() => {
    fetchProfile(user.id);
  }, [user]); // Dispara a cada alteração de qualquer campo de user
  ```
- **Correto:** Passar apenas o ID primitivo:
  ```tsx
  useEffect(() => {
    fetchProfile(user.id);
  }, [user.id]);
  ```

---

### P3: Renderização Segura & UX (`render-`)

#### `render-conditional-ternary` — Use ternário explícito em vez de `&&`
No JSX do React, `{count && <Badge />}` renderizará o número `0` na tela caso `count === 0`.
- **Incorreto:**
  ```tsx
  {items.length && <List items={items} />} // Exibe "0" quando a lista está vazia!
  ```
- **Correto:**
  ```tsx
  {items.length > 0 ? <List items={items} /> : null}
  ```

#### `render-hoist-jsx` — Extraia JSX estático para fora do componente
Elementos JSX estáticos ou ícones que não dependem de props ou estado podem ser declarados no nível do módulo ou constantes estáveis, evitando que o React recrie a árvore de objetos virtuais em cada re-render.

#### `render-animate-wrapper` — Anime contêineres `div`, não elementos SVG puros
Ao animar ícones com Tailwind CSS (`animate-spin`, transições de opacidade/escala), aplique a classe em uma `div` ou `span` envoltória quando o nó SVG tiver atributos estritos de viewport (`viewBox`).

---

### P4: Bundle Size & Code Splitting com Vite (`bundle-`)

#### `bundle-lazy-routes` — Use `React.lazy` + `Suspense` em telas pesadas
Rotas secundárias, modais analíticos complexos ou editores pesados devem ser carregados sob demanda:
```tsx
import { lazy, Suspense } from 'react';

const DevTasksAnalyticsModal = lazy(() => import('./DevTasksAnalyticsModal'));

export function TaskView() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      {isOpen ? <DevTasksAnalyticsModal /> : null}
    </Suspense>
  );
}
```

#### `bundle-direct-imports` — Importações cirúrgicas de ícones e utilitários
- Importe ícones do `lucide-react` de forma direta ou nomeada padronizada, evitando carregar coleções inteiras.
- Mantenha funções utilitárias pequenas em `apps/web/src/lib/utils.ts` (ex: `cn` com `clsx` e `tailwind-merge`).

---

### P5: JavaScript & Estruturas de Dados (`js-`)

#### `js-index-maps` — Use `Map` / `Set` para buscas frequentes $O(1)$
Se um componente recebe centenas de itens (ex: logs de auditoria, permissões de workspace ou tarefas) e precisa checar correspondências repetidamente:
```tsx
// Incorreto: O(N * M) com includes em loop
const hasPermission = (id: string) => allowedIds.includes(id);

// Correto: O(1) usando Set memoizado
const allowedSet = useMemo(() => new Set(allowedIds), [allowedIds]);
const hasPermission = (id: string) => allowedSet.has(id);
```

#### `js-early-exit` — Saídas precoces (Guard Clauses)
Evite aninhamento profundo de blocos `if/else`. Trate estados de carregamento, erros ou ausência de dados primeiro:
```tsx
export function WorkspaceCard({ workspace }: WorkspaceCardProps) {
  if (!workspace) {
    return <WorkspaceCardSkeleton />;
  }

  return (
    <div className="rounded-lg border p-4">
      <h3>{workspace.name}</h3>
    </div>
  );
}
```

---

## 4. Checklist Rápido de Code Review Frontend

Antes de enviar ou aprovar alterações no frontend:
- [ ] Não há `condition && <Component />` suscetível ao bug do número `0`?
- [ ] O estado derivado não está sendo duplicado com `useState` + `useEffect`?
- [ ] As atualizações de estado em callbacks utilizam a assinatura funcional `setState(prev => ...)` quando apropriado?
- [ ] O código utiliza os hooks gerados do Orval/TanStack Query sem reinventar chamadas brutas de `fetch`?
- [ ] O comando de guardrail do projeto passou com sucesso?
  ```bash
  python tools/scripts/verify.py
  ```
