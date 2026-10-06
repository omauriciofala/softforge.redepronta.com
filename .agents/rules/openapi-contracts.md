# Regras de Contratos: OpenAPI 3.1 & Pydantic v2

## Boas Práticas para Schemas de API:
1. **ConfigDict(from_attributes=True):** Todo schema de resposta que lê dados diretamente de instâncias SQLAlchemy DEVE declarar `model_config = ConfigDict(from_attributes=True)`.
2. **Descrições Explícitas:** Use `Field(description="...")` em campos importantes. Isso enriquece a documentação interativa e permite que agentes de IA e clientes de API entendam a semântica de cada propriedade.
3. **Imutabilidade e Tipagem Estrita:** Utilize tipos precisos como `uuid.UUID`, `datetime`, `EmailStr` e `Literal[...]` em vez de strings genéricas.
4. **Exportação Automática:** Toda adição de rota ou alteração de modelo deve ser seguida da execução de `python tools/scripts/export_openapi.py`.
