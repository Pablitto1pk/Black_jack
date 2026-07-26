# Black_jack
  Projekt gry w BlackJacka napisany w pythonie. Projekt zakłada stworzenie działającej gry, z możliwością symulacji rozgrywania przez wielu graczy AI, bazy danych wyników, następnie analizy danych średnich strat gracza, wpływ zastosowania sieci neuronowej wyszkolonej na optymalnej metodzie gry, a następnie zbadanie wpływu zastosowania sieci neuronowej ze zliczaniem kart by zbadać wpływ optymalnej strategii, liczenia kart, manipulacji rozmiaru Bet'u oraz zlokalizowania w bucie (ang. shoe) karty kończoncej rozdanie na średnie Expected Value dla stałego betu i potencjalne zyski przy zmiennym bet size.

## Instalacja i uruchomienie (Windows, `uv`)

Projekt uzywa [`uv`](https://docs.astral.sh/uv/) jako menedzera pakietow i srodowisk -
**nie** Anacondy. Jesli w terminalu widzisz prefiks `(base)` przed nazwa venv,
to Anaconda automatycznie aktywuje sie w kazdej nowej powloce (pozostalosc po
wczesniejszej instalacji) - mozna to wylaczyc jednorazowo komenda
`conda config --set auto_activate_base false` (nie jest to wymagane, ale
zmniejsza pomylki co do tego, ktory Python jest faktycznie uzywany).

### 1. Instalacja `uv` (raz, na cala maszyne)

W PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Zamknij i otworz nowe okno PowerShell (zeby zaktualizowany `PATH` zadzialal),
sprawdz instalacje:

```powershell
uv --version
```

### 2. Instalacja projektu i zaleznosci

Z korzenia repo (`Black_jack/`, tam gdzie lezy `pyproject.toml`):

```powershell
uv sync
```

Ta jedna komenda: tworzy/aktualizuje `.venv`, instaluje wszystkie zaleznosci
(`pandas`, `matplotlib`, `jupyter`) z `pyproject.toml`, tworzy plik `uv.lock`
(zapewnia powtarzalne wersje pakietow), i **instaluje sam pakiet `blackjack`
w trybie edytowalnym** - to ostatnie jest kluczowe: dzieki temu
`from blackjack.xxx import yyy` dziala poprawnie w kazdym pliku projektu,
niezaleznie skad i jak jest odpalany (bezposrednio, przez VS Code, przez
`-m`), bo Python znajduje pakiet `blackjack` przez `site-packages`, a nie
przez zgadywanie folderu na podstawie sciezki uruchamianego pliku.

### 3. Uruchamianie

Dwie opcje, obie poprawne:

**A) Z aktywnym venv** (klasyczne podejscie):

```powershell
.venv\Scripts\Activate.ps1
python main.py
python simulation.py
```

**B) Bez aktywacji, przez `uv run`** (automatycznie synchronizuje env przed
uruchomieniem):

```powershell
uv run python main.py
uv run python simulation.py
```

### 4. VS Code - interpreter i kernel Jupytera

VS Code czasem domyslnie wybiera interpreter/kernel Anacondy (`base`) zamiast
lokalnego `.venv` projektu - to nie jest blad, tylko trzeba go raz wskazac
recznie:

- **Zwykle pliki `.py`** (`Ctrl+Shift+P` -> "Python: Select Interpreter") ->
  wybierz ten w `.venv\Scripts\python.exe` (powinien pojawic sie na liscie
  jako np. `.venv (Python 3.x)` po `uv sync`).
- **Notebook `sprawozdanie.ipynb`** - kliknij wybor kernela w prawym gornym
  rogu -> "Select Another Kernel" -> **"Python Environments..."** -> wybierz
  ten sam `.venv`. Jesli nie pojawia sie na liscie: "Enter interpreter
  path..." i recznie wskaz `Black_jack\.venv\Scripts\python.exe`. Zeby
  kernel w ogole mial co pokazac, `.venv` musi miec zainstalowany `jupyter`/
  `ipykernel` - `uv sync` juz to robi (patrz krok 2), wiec zazwyczaj
  wystarczy sam wybor srodowiska.

### Co to jest `blackjack.egg-info/`?

Folder tworzony automatycznie przez `pip`/`uv` przy instalacji edytowalnej
(`uv sync` / `pip install -e .`) - to metadane pakietu (`PKG-INFO`,
`SOURCES.txt`, `requires.txt`, `top_level.txt`), NIE Twoj kod. Pozwala
Pythonowi "wiedziec", ze pakiet `blackjack` jest zainstalowany i gdzie go
szukac. Bezpieczny do skasowania (odtworzy sie przy kolejnym `uv sync`),
i juz jest w `.gitignore` (sekcja "Distribution / packaging", wzorzec
`*.egg-info/`) - nie trafia do gita.
