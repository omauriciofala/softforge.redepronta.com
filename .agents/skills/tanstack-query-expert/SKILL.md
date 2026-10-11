---
name: tanstack-query-expert
description: "Expert em TanStack Query v5 no SoftForge (Vite SPA). Gerenciamento de estado assíncrono, hooks autogerados pelo Orval, Query Key Factories, mutações com Optimistic Updates e invalidação cirúrgica de cache."
risk: safe
source: community-adapted
date_added: "2026-10-11"
---

# TanStack Query Expert (SoftForge)

Guia definitivo de gerenciamento de estado assíncrono e cache para o frontend do SoftForge (**Vite 5 + React 18 SPA + TanStack Query v5 + Orval**).

---

## 1. Princípios Inegociáveis

1. **Nunca use `useEffect` + `useState` para data fetching:** Se os dados vêm da API do backend FastAPI, o TanStack Query é o único responsável por buscar, cachear e sincronizar esse estado.
2. **Priorize os Hooks Autogerados pelo Orval:** Os contratos OpenAPI 3.1 do backend geram hooks tipados em `apps/web/src/api/generated/`. Nunca escreva `fetch` ou `axios` manuais quando houver hook gerado.
3. **Não duplique dados em `useState`:** Consuma `data` diretamente do hook. Se precisar filtrar, ordenar ou transformar dados, faça-o inline durante o render ou com `useMemo`.

---

## 2. Consumo dos Hooks Gerados pelo Orval

O Orval gera clientes fortemente tipados baseados no OpenAPI do FastAPI em `src/api/generated/<fatia>/`:

```typescript
import { 
  useListWorkspacesApiV1WorkspacesGet,
  useCreateWorkspaceApiV1WorkspacesPost,
  getListWorkspacesApiV1WorkspacesGetQueryKey 
} from '@/api/generated/workspaces-multi-tenancy/workspaces-multi-tenancy';

export function WorkspacesList() {
  // Query automática com cache global de 5 minutos (configurado em App.tsx)
  const { data: workspaces, isLoading, isError } = useListWorkspacesApiV1WorkspacesGet();
  
  if (isLoading) return <WorkspacesSkeleton />;
  if (isError) return <ErrorMessage text="Erro ao carregar workspaces" />;

  return (
    <ul>
      {workspaces?.map((ws) => (
        <li key={ws.id}>{ws.name}</li>
      ))}
    </ul>
  );
}
```

---

## 3. Mutações e Invalidação Cirúrgica de Cache

Ao criar, editar ou excluir dados no backend, invalide a chave de cache correspondente exportada pelo próprio Orval para que a UI sincronize automaticamente em segundo plano:

```typescript
import { useQueryClient } from '@tanstack/react-query';
import { 
  useCreateWorkspaceApiV1WorkspacesPost,
  getListWorkspacesApiV1WorkspacesGetQueryKey 
} from '@/api/generated/workspaces-multi-tenancy/workspaces-multi-tenancy';

export function useCreateWorkspaceAction() {
  const queryClient = useQueryClient();
  const createMutation = useCreateWorkspaceApiV1WorkspacesPost({
    mutation: {
      onSuccess: () => {
        // Invalida cirurgicamente a lista usando a QueryKey oficial do contrato
        queryClient.invalidateQueries({
          queryKey: getListWorkspacesApiV1WorkspacesGetQueryKey(),
        });
      },
    },
  });

  return createMutation;
}
```

---

## 4. Optimistic Updates (Atualizações Otimistas)

Para operações onde a interface deve responder instantaneamente ao clique do usuário (ex: alterar status de tarefa no slice de `dev_tasks`, renomear item ou marcar notificação como lida):

```typescript
import { useQueryClient } from '@tanstack/react-query';

export function useOptimisticToggleTask() {
  const queryClient = useQueryClient();

  return useUpdateTaskMutation({
    mutation: {
      onMutate: async (updatedTask) => {
        // 1. Cancela queries em voo para evitar sobreposição
        await queryClient.cancelQueries({ queryKey: ['tasks', updatedTask.id] });

        // 2. Salva snapshot do valor anterior para rollback
        const previousTask = queryClient.getQueryData(['tasks', updatedTask.id]);

        // 3. Atualiza o cache imediatamente
        queryClient.setQueryData(['tasks', updatedTask.id], (old: any) => ({
          ...old,
          ...updatedTask,
        }));

        // Retorna o contexto com o snapshot
        return { previousTask };
      },
      onError: (err, newTodo, context) => {
        // 4. Se falhar, reverte para o estado anterior
        if (context?.previousTask) {
          queryClient.setQueryData(['tasks', newTodo.id], context.previousTask);
        }
      },
      onSettled: (data, error, variables) => {
        // 5. Sempre refaz o fetch ao final para garantir consistência
        queryClient.invalidateQueries({ queryKey: ['tasks', variables.id] });
      },
    },
  });
}
```

---

## 5. Configurações Globais no SoftForge (`App.tsx`)

A instância mestre do `QueryClient` está centralizada em `apps/web/src/App.tsx`:
- `staleTime: 1000 * 60 * 5` (dados são considerados frescos por 5 minutos; remounts de componentes não disparam requisições de rede desnecessárias).
- `retry: 1` (apenas uma tentativa adicional em caso de falha de rede para evitar sobrecarga).

---

## 6. Checklist de Boas Práticas

- [ ] Os dados foram obtidos através dos hooks autogerados em `src/api/generated/`?
- [ ] A mutação está usando a função `getQueryKey()` do Orval para invalidação?
- [ ] Nenhum dado assíncrono foi copiado para um `useState` local redundante?
- [ ] Operações críticas de UX utilizam `onMutate` com rollback seguro no `onError`?
