# Guion del video "La portada de The Economist 2027, descifrada".
# Cada escena: etiqueta, título, cajas de recorte (x0, y0, lado) sobre la portada
# original de 608x812 px (inicio -> fin, para el zoom/paneo), frases narradas
# y referencias que aparecen en pantalla.

ESCENAS = [
    dict(
        tag="INTRO", title="La portada que\npredice 2027",
        box=[(-102, 0, 812), (40, 190, 530)],
        lines=[
            "Cada noviembre, The Economist publica The World Ahead, su apuesta sobre el año que viene.",
            "Esta es la portada de 2027: más de cincuenta símbolos dentro de un solo círculo.",
            "Vamos a descifrarlos uno por uno, y a compararlos con lo que está pasando hoy.",
        ],
        refs="The Economist · The World Ahead 2027 (publicada el 16-nov-2026)",
    ),
    dict(
        tag="LOS TITULARES", title="Seis temas\nen la tapa",
        box=[(90, 120, 430), (100, 130, 410)],
        lines=[
            "La portada anuncia sus temas: el capítulo final de Trump, que no se irá en silencio.",
            "La inteligencia artificial: aceleración, riesgos y reacción. Y lo que viene después de Irán.",
            "El clima, con otro año récord de calor. El auge del populismo. Y la fatiga de franquicias en Hollywood.",
        ],
        refs="Texto de portada · The World Ahead 2027",
    ),
    dict(
        tag="01 · EL PODER", title="La cima:\nla era post Trump",
        box=[(200, 195, 200), (225, 200, 160)],
        lines=[
            "En la cima, una fila de líderes en traje entre banderas rojas: el poder como escenario.",
            "Para The Economist, en 2027 empieza la era post Trump. Él no puede volver a postularse en 2028.",
            "Y las elecciones de medio mandato del 3 de noviembre ya castigaron a los republicanos.",
            "Pero, como advierte la portada, no se irá en silencio.",
        ],
        refs="Tom Standage, editor de The World Ahead · Elecciones de medio mandato EE. UU., 3-nov-2026",
    ),
    dict(
        tag="02 · INSTITUCIONES", title="Columnas\ny custodia",
        box=[(190, 290, 130), (200, 300, 110)],
        lines=[
            "Debajo, un edificio de columnas, como un tribunal o un banco central, con figuras que salen custodiadas.",
            "Es el choque entre el poder y las instituciones: jueces, fiscales y bancos centrales.",
            "Ese pulso marcará el último tramo de la presidencia de Trump.",
        ],
        refs="Interpretación del símbolo · contexto político de EE. UU. 2026",
    ),
    dict(
        tag="03 · TRATOS", title="Hielo, apretón\nde manos y antena",
        box=[(185, 235, 150), (200, 245, 125)],
        lines=[
            "Un iceberg rojo, un apretón de manos y una antena que emite señales.",
            "Groenlandia y el Ártico, los acuerdos personales a puerta cerrada, y la guerra de la información.",
            "La diplomacia de esta época se hace a base de tratos.",
        ],
        refs="Interpretación del símbolo · interés de EE. UU. por Groenlandia (2025-2026)",
    ),
    dict(
        tag="04 · DESPUÉS DE IRÁN", title="El Golfo\ny Ormuz",
        box=[(330, 220, 180), (390, 500, 160)],
        lines=[
            "Arriba a la derecha, palmeras, un camello y una luna creciente: el Golfo.",
            "Y abajo, un petrolero encadenado, cazas en el aire y un mar teñido de rojo. Es el estrecho de Ormuz.",
            "La guerra con Irán de 2026 dejó un bloqueo naval estadounidense y ataques hutíes contra Arabia Saudita.",
            "Según datos del Pentágono, a Estados Unidos ya le costó más de 47 mil millones de dólares.",
        ],
        refs="Al Jazeera, blog en vivo (1 al 16-nov-2026) · Iran International · datos del Pentágono",
    ),
    dict(
        tag="05 · DEUDA", title="El gráfico\nque se desploma",
        box=[(295, 315, 150), (300, 320, 130)],
        lines=[
            "Un gráfico que se desploma, fajos de billetes, fichas de casino y un reloj de arena.",
            "Gasto público alto, inversión gigantesca en centros de datos y una inflación que regresa.",
            "The Economist advierte que pedir prestado será más caro para gobiernos, empresas y familias. El reloj corre.",
        ],
        refs="The World Ahead 2027 (vía Wealth Adviser y 1news.az, 17-nov-2026)",
    ),
    dict(
        tag="06 · RUSIA", title="El Kremlin\ny el jinete",
        box=[(425, 320, 140), (430, 330, 130)],
        lines=[
            "El Kremlin y un jinete a caballo: la imagen clásica de Putin.",
            "Rusia y Ucrania volvieron a negociar en Abu Dabi el 10 y 11 de noviembre, por primera vez desde febrero.",
            "Acordaron un canje de prisioneros, pero no un alto el fuego.",
            "Y el oleoducto roto, justo debajo, recuerda que la energía sigue siendo un arma.",
        ],
        refs="Al Jazeera, 17-nov-2026 · Al-Monitor, nov-2026 · conversaciones de Abu Dabi",
    ),
    dict(
        tag="07 · CHINA Y TAIWÁN", title="La bandera\ny los misiles",
        box=[(40, 335, 180), (40, 440, 180)],
        lines=[
            "A la izquierda, la bandera china, una multitud disciplinada y hombres en traje.",
            "Más abajo, misiles rojos en formación.",
            "Según la inteligencia estadounidense, Xi Jinping pidió a su ejército estar listo para tomar Taiwán en 2027.",
            "The Economist lo señala como uno de los grandes riesgos del año.",
        ],
        refs="The World Ahead 2027 (vía ua.news y Türkiye Today) · CIA, declaraciones de 2023",
    ),
    dict(
        tag="08 · INTELIGENCIA ARTIFICIAL", title="Un cerebro\nde circuitos",
        box=[(110, 395, 250), (255, 420, 100)],
        lines=[
            "En el corazón del círculo, literalmente, hay un cerebro de circuitos.",
            "A su lado, un robot que se desarma entre chips y ceros y unos, y una camioneta eléctrica enchufada.",
            "The Economist advierte sobre la deuda de las empresas de inteligencia artificial en acuerdos opacos.",
            "Y sobre modelos cada vez más capaces usados para ciberataques.",
        ],
        refs="The World Ahead 2027 (vía Incrypted y 1news.az, nov-2026)",
    ),
    dict(
        tag="09 · OZEMPIC", title="Jeringas, pastillas\ny laboratorio",
        box=[(200, 420, 200), (225, 440, 150)],
        lines=[
            "Una jeringa, pastillas y un laboratorio lleno de frascos y labiales.",
            "Son los fármacos para adelgazar, como Ozempic.",
            "The Economist prevé que su efecto vaya más allá de la salud: cambian lo que comemos, compramos y consumimos.",
        ],
        refs="The World Ahead 2027 (vía Wealth Adviser, nov-2026)",
    ),
    dict(
        tag="10 · ASIA", title="La Puerta de la India\ny la pagoda",
        box=[(155, 455, 120), (190, 590, 110)],
        lines=[
            "La Puerta de la India, en Nueva Delhi, y más abajo una pagoda junto al símbolo del yen.",
            "India, la gran economía que más crece, y Japón, entre un yen débil y tensiones con China,",
            "completan el tablero asiático.",
        ],
        refs="Interpretación del símbolo",
    ),
    dict(
        tag="11 · FRANCIA", title="¿Qué es más\npoderoso que Le Pen?",
        box=[(335, 395, 230), (345, 405, 170)],
        lines=[
            "Una estatua con antorcha sobre una multitud parisina, una bota militar y una urna.",
            "Francia elige presidente en abril de 2027.",
            "El 7 de julio, un tribunal de apelación mantuvo la condena de Marine Le Pen, pero le abrió la puerta a competir, con brazalete electrónico.",
            "Si no puede, su delfín Jordan Bardella toma el relevo. De ahí el juego de palabras: ¿qué es más poderoso que Le Pen?",
        ],
        refs="AP / ABC News, 7-jul-2026 · Al Jazeera, 9-jul-2026 · NPR",
    ),
    dict(
        tag="12 · GUERRA", title="Tanques, drones\ny ruinas",
        box=[(60, 520, 330), (200, 540, 190)],
        lines=[
            "En la franja inferior, tanques, drones, explosiones y ciudades en ruinas.",
            "Ucrania, Oriente Medio, Sudán.",
            "La portada no promete un 2027 en paz.",
        ],
        refs="Interpretación del símbolo",
    ),
    dict(
        tag="13 · CLIMA", title="El año más\ncaluroso, otra vez",
        box=[(35, 420, 120), (395, 590, 120)],
        lines=[
            "Un bosque en llamas con un ciervo que huye. Y al otro lado, un termómetro en rojo, un barril ardiendo y molinos de viento.",
            "La Organización Meteorológica Mundial advierte que un El Niño muy fuerte podría hacer de 2027 el año más caliente registrado.",
            "Superaría a 2024, que llegó a cerca de 1,55 grados sobre la era preindustrial.",
        ],
        refs="OMM, actualización de nov-2026 · Climate Home News, 28-may-2026",
    ),
    dict(
        tag="14 · ESPACIO", title="Satélites,\ncohetes y estaciones",
        box=[(80, 240, 130), (95, 250, 110)],
        lines=[
            "Arriba a la izquierda, un satélite, un cohete y un astronauta flotando.",
            "The Economist prevé que la nave Starship empiece lanzamientos regulares de satélites, y que despegue la primera estación espacial privada.",
            "Hasta los centros de datos en órbita sonarán menos descabellados.",
        ],
        refs="The World Ahead 2027 (vía Wealth Adviser, nov-2026)",
    ),
    dict(
        tag="15 · HOLLYWOOD", title="Fatiga\nde franquicias",
        box=[(105, 590, 120), (150, 600, 75)],
        lines=[
            "Un proyector y una cámara de cine antigua: Hollywood.",
            "2027 llega cargado de secuelas, de Superman a Batman y Minecraft, mientras la industria se reacomoda tras la venta de Warner Bros.",
            "La portada lo resume en dos palabras: fatiga de franquicias.",
        ],
        refs="TheWrap · Variety · AP (dic-2025) sobre la venta de Warner Bros.",
    ),
    dict(
        tag="16 · LA BOLA DE CRISTAL", title="Los que esperan",
        box=[(175, 595, 250), (265, 600, 140)],
        lines=[
            "Abajo del todo, una bola de cristal frente a una fila de personas que esperan.",
            "Y carpas rojas con familias desplazadas.",
            "Es la parte más honesta de la portada: los pronósticos fallan, pero las consecuencias siempre las pagan los mismos.",
        ],
        refs="Interpretación del símbolo",
    ),
    dict(
        tag="CIERRE", title="Todo está\nconectado",
        box=[(40, 190, 530), (0, 0, 812)],
        lines=[
            "Rojo, negro y blanco. Guerra, dinero, tecnología y poder, dentro de un mismo círculo.",
            "El mensaje es claro: en 2027 todo está conectado.",
            "¿Qué símbolo crees que se cumplirá primero? Te leo en los comentarios.",
        ],
        refs="Portada: The Economist, The World Ahead 2027 · Análisis independiente",
    ),
]

# Pronunciación para la voz en español (lo que se muestra no cambia).
PRONUNCIA = {
    "The World Ahead": "De Uorld Ajéd",
    "The Economist": "De Ikónomist",
    "Trump": "Tromp",
    "Ozempic": "Ozémpic",
    "Starship": "Estárship",
    "Hollywood": "Jólibud",
    "Warner Bros": "Uórner Bros",
    "Superman": "Súperman",
    "Batman": "Bátman",
    "Minecraft": "Máincraft",
    "Jordan Bardella": "Yordán Bardelá",
    "Le Pen": "Le Pén",
    "Marine": "Marín",
    "Xi Jinping": "Shi Yinpín",
    "Abu Dabi": "Abu Dabi",
    "1,55": "uno coma cincuenta y cinco",
    "47 mil millones": "cuarenta y siete mil millones",
}
