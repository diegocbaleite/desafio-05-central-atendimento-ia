# Registro de conferência do OCR — 17/10/2026

Arquivo-fonte: `entrada_pdf-imagem.pdf` (1 página digitalizada).

**Confirmação humana recebida:** o usuário confirmou explicitamente, nesta conversa, os 14 valores apresentados na tabela de conferência: código, nome, nascimento (12/08/2008), CPF (123.456.789-00), RG, naturalidade, nome da mãe, curso, carga horária, eixo tecnológico, turno, início do curso, e-mail e data da matrícula.

**Outras informações do formulário:** cabeçalho, avisos, rótulos e campos sem preenchimento foram transcritos por análise visual assistida do PDF. Não foram objeto da mesma confirmação campo a campo.

**Cuidado de avaliação:** a referência e a versão revisada foram geradas a partir da MESMA transcrição visual; seus conteúdos são idênticos. Logo, CER/WER de revisado versus referência igual a zero é consequência da construção dos arquivos e NÃO evidencia qualidade do Tesseract nem revisão independente do texto revisado. É útil calcular CER/WER do OCR BRUTO versus referência conferida, preservando o arquivo bruto original.

**Nota metodológica:** o escaneamento pode não capturar pequenos detalhes de pontuação; números confirmados pelo usuário prevalecem sobre a leitura preliminar. Os campos vazios aparecem com seus rótulos e sem valores para representar o documento original (não adicionar 'não localizado' como texto se ele não estiver impresso). A assinatura manuscrita é preservada como traço no PDF, sem transcrevê-la como se fosse texto legível de alta confiança.

**Integração no projeto:** colocar os dois `.txt` em um diretório de referências escolhido pela equipe, sem alterar `arquivos/entrada_pdf-imagem.pdf` nem `resultados/guilherme/.../ocr_bruto.txt`. Ajustar os caminhos no comando `--gabarito` e `--revisado` ao diretório efetivo. A execução de OCR feita localmente e os 41 testes relatados no contexto não foram reexecutados neste ambiente.
