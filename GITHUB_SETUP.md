# 🚀 Instruções para Publicar no GitHub

## 📋 Pré-requisitos

1. **Conta no GitHub:** [Criar conta](https://github.com/join) se ainda não tiver
2. **Git configurado:** Verifique se tem nome e email configurados:
   ```bash
   git config --global user.name "Seu Nome"
   git config --global user.email "seu.email@exemplo.com"
   ```

## 🔗 Passos para Publicar

### 1. Criar Repositório no GitHub

1. **Acesse:** [GitHub](https://github.com)
2. **Clique em:** "New repository" (botão verde)
3. **Configure:**
   - **Repository name:** `MeetAI`
   - **Description:** `🎙️ Gravador de Áudio com Resumos IA - Transcrição automática e resumos inteligentes`
   - **Visibilidade:** Public (ou Private se preferir)
   - **NÃO marque:** "Add a README file" (já temos um)
   - **NÃO marque:** "Add .gitignore" (já temos um)
   - **NÃO marque:** "Choose a license" (já temos um)
4. **Clique em:** "Create repository"

### 2. Conectar Repositório Local ao GitHub

No terminal do seu projeto (C:\Work\MeetAI), execute:

```bash
# Adicionar origin remoto (substitua 'seu-usuario' pelo seu username do GitHub)
git remote add origin https://github.com/seu-usuario/MeetAI.git

# Verificar se foi adicionado corretamente
git remote -v

# Renomear branch principal para 'main' (padrão GitHub)
git branch -M main

# Enviar código para GitHub
git push -u origin main
```

### 3. Verificar Upload

1. **Atualize a página** do seu repositório no GitHub
2. **Verifique se todos os arquivos** estão lá
3. **Confirme se o README.md** está sendo exibido na página inicial

## 🎯 Exemplo Completo

Supondo que seu usuário GitHub seja `joaosilva123`:

```bash
# No terminal, dentro da pasta C:\Work\MeetAI

# 1. Adicionar repositório remoto
git remote add origin https://github.com/joaosilva123/MeetAI.git

# 2. Renomear branch
git branch -M main

# 3. Enviar para GitHub
git push -u origin main
```

## 🔒 Autenticação

Se solicitar login, use:
- **Username:** Seu username do GitHub
- **Password:** **Personal Access Token** (não a senha da conta)

### Como criar Personal Access Token:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → Classic
3. Selecione: `repo` (acesso completo aos repositórios)
4. Generate token
5. **Copie o token** (não será mostrado novamente)
6. Use este token como "password" no Git

## ✅ Pronto!

Após executar os comandos, seu projeto estará disponível em:
`https://github.com/seu-usuario/MeetAI`

## 🔄 Para Futuras Atualizações

Sempre que fizer mudanças no código:

```bash
# Adicionar mudanças
git add .

# Fazer commit
git commit -m "📝 Descrição das mudanças"

# Enviar para GitHub
git push
```

## 🛠️ Comandos Úteis

```bash
# Ver status do repositório
git status

# Ver histórico de commits
git log --oneline

# Ver repositórios remotos
git remote -v

# Criar nova branch
git checkout -b nova-feature

# Trocar entre branches
git checkout main
git checkout nova-feature
```

---

**🎉 Seu projeto MeetAI estará público e disponível para toda a comunidade!**