try:
    from .tokens import Token, TokenType, delineators, delineatorTypes, operators, operatorTypes, keywords
except ImportError:
    from tokens import Token, TokenType, delineators, delineatorTypes, operators, operatorTypes, keywords

def potIdentifier(buffer, line_num, bufferStart):
    if buffer in delineatorTypes:
        return Token(delineatorTypes[buffer], buffer, line_num, bufferStart)
    if buffer in operatorTypes:
        return Token(operatorTypes[buffer], buffer, line_num, bufferStart)
    if buffer in keywords:
        return Token(keywords[buffer], buffer, line_num, bufferStart)
    if buffer.isdigit():
        return Token(TokenType.NUMBER, buffer, line_num, bufferStart)
    return Token(TokenType.IDENTIFIER, buffer, line_num, bufferStart)

def tokenize(file):
    tokens = []
    for line_num, content in enumerate(file, 1):
        line = content.rstrip()
        buffer = ""
        bufferStart = 0
        charStatus = False
        i = 0
        while i < len(line):
            c = line[i]
            if charStatus:
                if c == '"':
                    charStatus = False
                    tokens.append(Token(TokenType.STRING, buffer, line_num, bufferStart))
                    buffer = ""
                    bufferStart = i + 1
                else:
                    buffer += c
                i += 1
                continue
            elif c == '"':
                charStatus = True
                bufferStart = i
                i += 1
            elif c in delineators or c in operators or c == " " or c == "!":
                if buffer:
                    tokens.append(potIdentifier(buffer, line_num, bufferStart))
                    buffer = ""
                
                if c in delineators or c in operators:
                    if i + 1 < len(line):
                        two_char = c + line[i + 1]
                        if two_char in ["==", "!="]:
                            tokens.append(potIdentifier(two_char, line_num, i))
                            i += 2
                            bufferStart = i
                            continue
                    
                    tokens.append(potIdentifier(c, line_num, i))
                
                bufferStart = i + 1
                i += 1
            else:
                if not buffer:
                    bufferStart = i
                buffer += c
                i += 1
        if buffer:
            tokens.append(potIdentifier(buffer, line_num, bufferStart))
    return tokens

