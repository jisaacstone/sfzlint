Linter and parser for .sfz files

CLI programs are mostly done.

Includes the `sfzlint` and `sfzlist` command line utilities
`sfzlint` will parse and validate sfzfiles. If a directory is passed it will be recursivly searched for sfz files.

    $ sfzlint path/to/file.sfz
    path/to/file.sfz:60:11:W continuous not one of ['no_loop', 'one_shot', 'loop_continuous', 'loop_sustain'] (loop_mode)
    path/to/file.sfz:98:18:W 8400 not in range -1 to 1 (fileg_depthccN)
    path/to/file.sfz:107:12:E expected integer got 0.1 (lfoN_freq)
    path/to/file.sfz:240:1:W unknown opcode (ampeg_sustain_curveccN)

`sfzlist` will print a list of known opcodes and metadata to stdout. Callig with `--path` will cause it to print opcodes found in that path

    $ sfzlist --path /sfz/instra/Scarypiano/
    amplitude_onccN aria Range(0,100) modulates=amplitude
    lokey v1 Range(0,127)
    ampeg_release_onccN v2 Alias(ampeg_releaseccN)
    label_ccN aria Any()
    bend_up v1 Range(-9600,9600)

## Features

* syntax validation
* checks opcodes against known opcodes on sfzformat.com
* validates opcode values when min or max or type are defined in the spec
* validates `*_curvecc` values above 7 have a corresponding `<curve>` header
* checks that sample files exists, also checks that case matches for portability with case-sensitive filesystems
* pulls in #includes and replaces vars from #defines

To build the linter I built a parser using [Lark](https://github.com/lark-parser/lark).

This may be useful to some people. I've also included the `sfz.lark` file.
The SFZ file format definition is vague. I had to make some assumptions. For example I assumed unquoted paths
cannot include newlines or `=`. Also I assume opcodes and note names are always lowercase.

    from sfzlint import parser
    lark_tree = parser.parse(sfz_string)

Opcode data is from [sfzformat.com](https://sfzformat.com/). If you see a bug in `syntax.yml` consider putting you PR
against [the source](https://github.com/sfzformat/sfzformat.github.io/blob/source/_data/sfz/syntax.yml)

## Installing

I've not put this on pypi yet. You can install with pip

    pip install git+git://github.com/jisaacstone/sfzlint.git

Or clone the repo and use `python setup.py install`

Both methods require python version >= 3.6

## To use with vim/neomake:

(This is what I built this thing for)

put the following in your .vimrc:

    au BufNewFile,BufRead *.sfz set filetype=sfz
    let g:neomake_sfz_enabled_makers=['sfzlint']
    let g:neomake_sfzlint_maker = {'exe': 'sfzlint', 'errorformat': '%f:%l:%c:%t %m'}
