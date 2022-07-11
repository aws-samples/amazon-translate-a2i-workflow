###
 # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 # SPDX-License-Identifier: MIT-0
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy of this
 # software and associated documentation files (the "Software"), to deal in the Software
 # without restriction, including without limitation the rights to use, copy, modify,
 # merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 # permit persons to whom the Software is furnished to do so.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 # INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 # PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 # HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 # OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 # SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 # Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
#   SPDX-License-Identifier: MIT
######
import unittest
import re
from sentenceSegmenter import split_sentences
class TestSentenceSegmenter(unittest.TestCase):

    def test_sentencesegemented_en(self):
        content = """Just then another visitor entered the drawing room: Prince Andrew Bolkónski, the little princess’ husband. How are you? He was a very handsome young
                   man, of medium height, with firm, clearcut features. Everything about him, from his weary, bored expression to his quiet, measured step,
                   offered a most striking contrast to his quiet, little wife. It was evident that he not only knew everyone in the drawing room, but had
                   found them to be so tiresome that it wearied him to look at or listen to them. And among all these faces that he found so tedious, none seemed
                   to bore him so much as that of his pretty wife. He turned away from her with a grimace that distorted his handsome face, kissed Anna
                   Pávlovna’s hand, and screwing up his eyes scanned the whole company."""
        sentences = split_sentences( content, "english")
        print( 'No of sentences :',len(sentences))
        self.assertEqual( 7, len(sentences))
        for s in sentences:
            print( s )

    def test_ReqExPattern(self):
        pattern = "<t>(.*?)</t>"
        str = "hello this is <t>my test</t>"
        str1 = "<t>hello</t> this is my <t>test</t>"
        substring = re.search(pattern, str).group(1)
        print( "test_ReqExPattern", substring )
        substring = re.search(pattern, str1)
        print( "test_ReqExPattern", substring )

    def test_sentencesegemented_es(self):
        content = """Justo entonces otro visitante entró en la sala de estar: el príncipe Andrew Bolkónski, el marido de la pequeña princesa. ¿Cómo está usted? Era un joven muy guapo
hombre, de altura media, con rasgos firmes y claros. Todo sobre
él, desde su expresión cansada y aburrida hasta su paso tranquilo y medido,
ofreció un contraste sorprendente con su pequeña y tranquila esposa. Era
evidente que no sólo conocía a todos en el salón, sino que había
les pareció tan cansado que le cansaba mirar o escuchar
ellos. Y entre todos estos rostros que le parecieron tan tediosos, ninguno parecía
para aburrirlo tanto como el de su bonita esposa. Se apartó de
con una mueca que distorsionó su guapo rostro, besó a Anna
La mano de Pávlovna, y arruinando los ojos escaneó a toda la compañía."""
        sentences = split_sentences( content, "spanish")
        print( 'No of sentences :',len(sentences))
        self.assertEqual( 7, len(sentences))
        for s in sentences:
            print( s )


if __name__ == '__main__':
    unittest.main()
