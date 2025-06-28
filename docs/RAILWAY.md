# Robot-Crypt: Solucionando problemas no Railway

Este guia aborda os problemas específicos que podem ocorrer ao executar o Robot-Crypt no Railway e as respectivas soluções.

## Problema comum: Erro 451 na API da Binance

Um erro 451 indica restrição de acesso por região/IP. A Binance tem bloqueios geográficos e o Railway pode estar usando IPs de regiões bloqueadas.

### Soluções para o erro 451:

1. **Configurar um proxy/VPN**:

   Configure as variáveis de ambiente no Railway:
   
   - `HTTP_PROXY` - URL do proxy HTTP (ex: "http://user:pass@proxy.example.com:8080")
   - `HTTPS_PROXY` - URL do proxy HTTPS (ex: "http://user:pass@proxy.example.com:8080")
   
   Também há suporte para proxies SOCKS5:
   - `HTTP_PROXY` - URL do proxy SOCKS5 (ex: "socks5://user:pass@proxy.example.com:1080")
   - `HTTPS_PROXY` - URL do proxy SOCKS5 (ex: "socks5://user:pass@proxy.example.com:1080")

2. **Usar provedores de proxy confiáveis**:
   
   Alguns provedores de proxy que podem ser usados:
   - [Smartproxy](https://smartproxy.com/)
   - [Bright Data](https://brightdata.com/)
   - [Proxyrack](https://www.proxyrack.com/)

3. **Usar uma VPS em região permitida**:

   Em vez de usar o Railway, considere hospedar o bot em um servidor VPS em uma região que não tenha restrições da Binance.
   Algumas opções:
   - DigitalOcean (Singapura)
   - Linode (Frankfurt)
   - AWS EC2 (regiões asiáticas ou europeias)

## Configuração no Railway

1. Configure todas as variáveis de ambiente necessárias no dashboard do Railway:
   - Credenciais da Binance
   - Configuração de proxy (se necessário)
   - Parâmetros de trading
   - Token e chat ID do Telegram

2. Adicione as seguintes variáveis ao Railway para resolver problemas de IP:
   ```
   HTTP_PROXY=http://seu-proxy:porta
   HTTPS_PROXY=http://seu-proxy:porta
   ```

## Monitoramento e Logs

O Railway oferece visualização de logs embutida:

1. Acesse seu projeto no dashboard do Railway
2. Clique em "Deployments" e depois no deployment ativo
3. Vá para a aba "Logs" para ver os logs em tempo real

## Solução de Problemas Específicos do Railway

### Container reiniciando continuamente

1. Verifique se todas as variáveis de ambiente necessárias estão configuradas
2. Verifique os logs para identificar erros específicos
3. Caso veja erros de conexão com a Binance, verifique as variáveis de proxy

### Uso excessivo de recursos

Se o bot estiver consumindo muitos recursos:

1. Aumente o intervalo entre verificações: `CHECK_INTERVAL=600` (10 minutos)
2. Reduza o número de pares monitorados
3. Aumente os recursos alocados no plano do Railway

## Migrando do Railway para outro provedor

Se continuar tendo problemas com o Railway, considere migrar o bot para:

1. **VPS tradicional**: Maior controle sobre o ambiente
2. **Heroku**: Alternativa similar ao Railway
3. **AWS Lambda/Azure Functions**: Para execução com base em agendamentos
