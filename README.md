Linter and parser for .sfz files

Unfinished, expect bugs

Includes the `sfzlint` command line program:

    sfzlint path/to/file.sfz

To build the linter I built a parser using [Lark](https://github.com/lark-parser/lark).

This may be useful to some people. I've also included the `sfz.ebnf` file. It probably has bugs.
The SFZ file format definition is vague. I had to make some assumptions. For example I assumed unquoted paths
cannot include newlines or `=`. Also I assume opcodes and note names are always lowercase.

    from sfzlint.parser import parser
    lark_tree = parser().parse(sfz_string)

Opcode data is from [sfzformat.com](https://sfzformat.com/). I have observed some opcodes in my instruments that are not listed on sfzformat.
For example `pitch_ccN` `volume_onccN` and `fileg_depthccN`. Pondering weather ARIA treats `cc` and `oncc` as interchangeable,
though perhaps these are simply ignored by the player.

## Installing

I've not put this on pypi yet, as it is still buggy an incomplete. You can install with pip

    pip install git+git://github.com/jisaacstone/sfzlint.git

Or clone the repo and use `python setup.py install`

Both methods require python version >= 3.6

## To use with vim/neomake:

(This is what I built this thing for)

put the following in your .vimrc:

    au BufNewFile,BufRead *.sfz set filetype=sfz
    let g:neomake_sfz_enabled_makers=['sfzlint']
    let g:neomake_sfzlint_maker = {'exe': 'sfzlint', 'errorformat': '%f:%l:%c:%t %m'}
