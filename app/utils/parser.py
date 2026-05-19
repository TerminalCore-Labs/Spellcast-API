from app.interfaces.editor import Node

def parser_nodes(nodo: Node):
    segmentos = []

    if nodo.type == 'text':
        voz_actual = 'default'
        inflection = 'default'

        if nodo.marks:
            for mark in nodo.marks:
                if mark.type == 'tts':
                    voz_actual = mark.attrs.voice
                    inflection = mark.attrs.inflection
                    

        if nodo.text:
            nodo_text = nodo.text
            segmentos.append(
                {
                    "text": nodo_text,
                    "voice": voz_actual,
                    "inflection": inflection
                }
            )

    if nodo.content:
        for hijo in nodo.content:
            resultado_content = parser_nodes(hijo)
            segmentos.extend(resultado_content)
    return segmentos