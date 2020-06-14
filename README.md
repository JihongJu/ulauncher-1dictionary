# Demo Extension


## Usage


## Custom dictionary

1. Overwrite the default vocabulary located at `~/.local/share/ulauncher/extensions/com.github.jihongju.ulauncher-1dictionary/1vocabulary.txt` with your own vocabulary. Note that the vocabulary is a newline-delimited text file. The default vocabulary is a Dutch vocabulary. You could download vocabulary for other languages at [JUST WORDS!](http://www.gwicks.net/dictionaries.htm).

2. Change the default online dictionary from Linguee (ducth-english) to the one fits you the best, for example, 

Website             | Language (source-target | Query 
--- | --- | --- 
[Merriam-Webster](https://www.merriam-webster.com/) | en-en | https://www.merriam-webster.com/dictionary/%s
[Linguee](https://www.linguee.com/)                 | nl-en | https://www.linguee.com/dutch-english/search?source=auto&query=%s


## Development
1. (Exit Ulauncher if it's running) Run
```ulauncher --no-extensions --dev -v```

2. (In another terminal) Run
```
VERBOSE=1 ULAUNCHER_WS_API=ws://127.0.0.1:5054/ulauncher-demo PYTHONPATH=$HOME/src/Ulauncher /usr/bin/python3 $HOME/.local/share/ulauncher/extensions/ulauncher-demo/main.py
```


## Reference

1. [Linguee](https://www.linguee.nl/)
2. [JUST WORDS!](http://www.gwicks.net/dictionaries.htm)

