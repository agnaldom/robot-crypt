# 🔐 Sistema de Autenticação Robot-Crypt

## ✅ Sistema Configurado e Funcionando!

O sistema de autenticação está **completamente funcional** com:

- ✅ **Superadmin criado automaticamente** na inicialização
- ✅ **Tokens JWT seguros** com validação rigorosa
- ✅ **Frontend de demonstração** para login
- ✅ **API RESTful** para integração

---

## 🔑 Credenciais do Superadmin

```
Email: agnaldo@qonnect.com.br
Senha: @G071290nm
```

**Estas credenciais são carregadas automaticamente do arquivo `.env`**

---

## 🚀 Como Usar

### 1. **Iniciar o Backend**

```bash
# No diretório do projeto
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

O superadmin será criado automaticamente na inicialização.

### 2. **Abrir o Frontend**

```bash
# Abrir no navegador
open frontend/login.html
```

Ou navegue até: `file:///caminho/para/robot-crypt/frontend/login.html`

### 3. **Fazer Login**

- Use as credenciais do superadmin
- Clique em "Fazer Login"
- O token JWT será gerado automaticamente
- Use o botão "Testar API" para verificar se funciona

---

## 🌐 APIs Disponíveis

### **Login (Obter Token)**
```bash
curl -X POST 'http://localhost:8000/auth/login' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'username=agnaldo@qonnect.com.br&password=@G071290nm'
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### **Verificar Token**
```bash
curl -H 'Authorization: Bearer SEU_TOKEN_AQUI' \
     http://localhost:8000/auth/me
```

### **Outras APIs Protegidas**
```bash
# Portfolio
curl -H 'Authorization: Bearer SEU_TOKEN_AQUI' \
     http://localhost:8000/portfolio

# Trading Sessions
curl -H 'Authorization: Bearer SEU_TOKEN_AQUI' \
     http://localhost:8000/trading-sessions

# Market Data
curl -H 'Authorization: Bearer SEU_TOKEN_AQUI' \
     http://localhost:8000/market
```

---

## 🔧 Token JWT - Detalhes Técnicos

### **Configuração de Segurança:**
- **Algoritmo:** HS256
- **Expiração:** 30 minutos
- **Claims obrigatórios:** sub, exp, iat, nbf, iss, aud
- **Validação rigorosa** de timestamps e origem

### **Estrutura do Token:**
```json
{
  "sub": "3",                           // User ID
  "exp": 1751937374,                   // Expiration time
  "iat": 1751935574,                   // Issued at
  "nbf": 1751935574,                   // Not before
  "iss": "robot-crypt-api",            // Issuer
  "aud": "robot-crypt-client"          // Audience
}
```

---

## 🔗 Integração Frontend

### **JavaScript Exemplo:**

```javascript
// 1. Fazer Login
async function login(email, password) {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    return data.access_token;
}

// 2. Usar Token nas Requisições
async function callAPI(token, endpoint) {
    const response = await fetch(`http://localhost:8000${endpoint}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    
    return response.json();
}

// 3. Exemplo de Uso
const token = await login('agnaldo@qonnect.com.br', '@G071290nm');
const userData = await callAPI(token, '/auth/me');
const portfolio = await callAPI(token, '/portfolio');
```

---

## 🛡️ Recursos de Segurança

### **Implementados:**
- ✅ **Hashing Argon2** para senhas
- ✅ **JWT com claims rigorosos**
- ✅ **CORS configurado**
- ✅ **Rate limiting** (produção)
- ✅ **Headers de segurança**
- ✅ **Validação de timestamps**
- ✅ **Proteção contra replay attacks**

### **Middleware de Segurança:**
- `SecurityHeadersMiddleware`
- `RateLimitMiddleware`
- `SecurityMonitoringMiddleware`
- `TrustedHostMiddleware`

---

## 📱 Próximos Passos

Para um frontend completo, considere implementar:

1. **Framework Frontend:**
   - React.js
   - Vue.js
   - Angular

2. **Funcionalidades:**
   - Dashboard de trading
   - Gráficos em tempo real
   - Gerenciamento de portfólio
   - Configuração de estratégias

3. **Autenticação Avançada:**
   - Refresh tokens
   - Logout seguro
   - Múltiplas sessões
   - 2FA (autenticação de dois fatores)

---

## 🧪 Testando o Sistema

Execute o script de teste:

```bash
python test_superadmin.py
```

**Resultado esperado:**
```
============================================================
🤖 Robot-Crypt - Teste de Superadmin e Token
============================================================

📋 Configurações do usuário:
   Email: agnaldo@qonnect.com.br
   Nome: Agnaldo Marinho
   Database: crossover.proxy.rlwy.net:36298/railway

🚀 Criando/verificando superadmin...
✅ Superadmin: agnaldo@qonnect.com.br (ID: 3)

🔐 Testando autenticação...
✅ Autenticação bem-sucedida: agnaldo@qonnect.com.br

🎫 Gerando token JWT...
✅ Token gerado com sucesso!
```

---

## ❓ Troubleshooting

### **Erro de CORS:**
Certifique-se de que o backend está configurado para aceitar requisições do frontend.

### **Token Expirado:**
Faça login novamente para obter um novo token (tokens expiram em 30 minutos).

### **Backend Offline:**
Certifique-se de que o backend está rodando em `http://localhost:8000`.

---

## 🎯 Resumo

**O sistema está 100% funcional para:**
- ✅ Login com email/senha
- ✅ Geração de tokens JWT seguros
- ✅ Autenticação de APIs
- ✅ Frontend de demonstração
- ✅ Criação automática de superadmin
- ✅ Integração com banco PostgreSQL

**Para usar em produção, apenas ajuste:**
- URLs do backend
- Configurações de CORS
- Certificados SSL/HTTPS
