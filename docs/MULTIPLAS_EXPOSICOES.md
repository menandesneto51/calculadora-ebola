# Múltiplas exposições — V17

A V16 representa o contato principalmente pela data do último contato. A V17 preserva esse campo para compatibilidade, mas introduz a relação **1 contato → N exposições**.

Cada exposição possui `exposure_id`, `event_id`, `contact_id`, `source_case_id`, início/fim, tipo, local e observação.

A última exposição efetiva passa a ser derivada pelo maior `end_date` do histórico. Sem histórico estruturado, `data_ultimo_contato` permanece como fallback legado.

Isso preserva exposições anteriores e permite reconstrução temporal e de múltiplas fontes.
