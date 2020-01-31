import re
from numbers import Real
from .errors import ValidationError, ValidationWarning
from .spec import version_hierarchy


class Validator:
    def validate(self, token, *args):
        raise NotImplementedError


class Any(Validator):
    def validate(self, token, *args):
        return None


class Min(Validator):
    def __init__(self, minimum):
        self.minimum = minimum

    def validate(self, token, *args):
        if token.value < self.minimum:
            return f'{token} less than minimum of {self.minimum}',


class Range(Validator):
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def validate(self, token, *args):
        if not self.low <= token.value <= self.high:
            return f'{token} not in range {self.low} to {self.high}'


class Choice(Validator):
    def __init__(self, choices):
        self.choices = choices

    def validate(self, token, *args):
        if token.value not in self.choices:
            subbed = OpcodeIntRepl.sub(token)
            if subbed not in self.choices:
                return f'{token.value} not one of {self.choices}'


class VersionValidator(Validator):
    def __init__(self, **mappings):
        self.mappings = mappings

    def validate(self, token, version):
        if version in self.mappings:
            return self.mappings[version].validate(token)
        elif 'default' in self.mappings:
            return self.mappings['default'].validate(token)


class Alias(Validator):
    def __init__(self, name):
        self.name = name

    def validate(self, token, *args):
        return opcodes[self.name]['validator'].validate(token, *args)


class OpcodeIntRepl:
    '''Converts opcodes with numeric components to their index form, and validates

    for example: OpcodeIntRepl.sub('eq3_bwcc25') -> 'eqN_bwccX'
    validates control codes in cc range.
    for example: OpcodeIntRepl.sub('eq3_bwcc256') -> ValidationError
    '''

    subs = ['N', 'X', 'Y']
    re = r'([a-z]*)(\d+)'
    # Some opcodes have numbers in the name, we ignore
    ignore = {'vel2', 'cutoff2', 'resonance2', 'wave2'}

    @classmethod
    def sub(cls, token):
        return re.sub(cls.re, cls(token), token.value)

    def __init__(self, raw_opcode):
        self.index = 0
        self.raw = raw_opcode

    def __call__(self, match):
        if match.group() in self.ignore:
            return match.group()
        try:
            sub = self.subs[self.index]
            self.index += 1
        except IndexError:
            raise ValidationError(
                f'{self.raw} is not a valid opcode: '
                'unexpected number at {match.group()}',
                self.raw)
        pre, num = match.groups()
        if pre.endswith('cc') and int(num) > 127:
            raise ValidationWarning(
                f'{num} is not a valid control code',
                self.raw)
        return pre + sub


def validate_opcode_expr(raw_opcode, token, spec_version):
    if raw_opcode not in opcodes:
        opcode = OpcodeIntRepl.sub(raw_opcode)
    else:
        opcode = raw_opcode.value

    try:
        validation = opcodes[opcode]
    except KeyError:
        raise ValidationWarning(
            f'unknown opcode ({opcode})',
            raw_opcode)
    v_type = validation.get('type')
    if v_type and not isinstance(token.value, v_type):
        raise ValidationError(
            f'expected {typenames[v_type]} got {token.value} ({opcode})',
            token)
    if validation['ver'] not in version_hierarchy[spec_version]:
        raise ValidationError(
            f'opcode is only in sfz spec {validation["ver"]}', raw_opcode)
    err_msg = validation['validator'].validate(token, spec_version)
    if err_msg:
        msg = f'{err_msg} ({opcode})'
        raise ValidationWarning(msg, token)


typenames = {
    int: 'integer',
    Real: 'integer or float',
    str: 'string',
}


opcodes = {
    'count':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 4294967296)},
    'delay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'delay_ccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'delay_onccN':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('delay_ccN')},
    'delay_random':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'end':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 4294967296)},
    'loop_mode':
        {'ver': 'v1', 'type': str,
         'validator': Choice(
             {'no_loop', 'one_shot', 'loop_continuous', 'loop_sustain'})},
    'loopmode':
        {'ver': 'v2', 'type': str,
         'validator': Alias('loop_mode')},
    'loop_start':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 4294967296)},
    'loopstart':
        {'ver': 'v2', 'type': int,
         'validator': Alias('loop_start')},
    'loop_end':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 4294967296)},
    'loppend':
        {'ver': 'v2', 'type': int,
         'validator': Alias('loop_end')},
    'offset':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 4294967296)},
    'offset_ccN':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 4294967296)},
    'offset_onccN':
        {'ver': 'v2', 'type': int,
         'validator': Alias('offset_ccN')},
    'offset_random':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 4294967296)},
    'sample':
        {'ver': 'v1', 'type': str,
         'validator': Any()},
    'sync_beats':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 32)},
    'sync_offset':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 32)},
    'group':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 4294967296)},
    'polyphony_group':
        {'ver': 'aria', 'type': int,
         'validator': Alias('group')},
    'off_by':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 4294967296)},
    'off_mode':
        {'ver': 'v1', 'type': str,
         'validator': Choice({'fast', 'normal', 'time'})},
    'output':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 1024)},
    'key':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'lokey':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'hikey':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'lovel':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'hivel':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'lochan':
        {'ver': 'v1', 'type': int,
         'validator': Range(1, 16)},
    'hichan':
        {'ver': 'v1', 'type': int,
         'validator': Range(1, 16)},
    'loccN':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'hiccN':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'lobend':
        {'ver': 'v1', 'type': int,
         'validator': Range(-8192, 8192)},
    'hibend':
        {'ver': 'v1', 'type': int,
         'validator': Range(-8192, 8192)},
    'sw_lokey':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'sw_hikey':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'sw_last':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'sw_down':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'sw_up':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'sw_previous':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'sw_vel':
        {'ver': 'v1', 'type': str,
         'validator': Choice({'current', 'previous'})},
    'lobpm':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 500)},
    'hibpm':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 500)},
    'lochanaft':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'hichanaft':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'lopolyaft':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'hipolyaft':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'lorand':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 1)},
    'hirand':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 1)},
    'seq_length':
        {'ver': 'v1', 'type': int,
         'validator': Range(1, 100)},
    'seq_position':
        {'ver': 'v1', 'type': int,
         'validator': Range(1, 100)},
    'trigger':
        {'ver': 'v1', 'type': str,
         'validator': Choice(
             {'attack', 'release', 'first', 'legato', 'release_key'})},
    'on_loccN':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'on_hiccN':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'pan':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'position':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'volume':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-144, 6)},
    'gain_ccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-144, 48)},
    'gain_onccN':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('gain_ccN')},
    'volume_onccN':
        {'ver': 'aria', 'type': Real,
         'validator': Alias('gain_ccN')},
    'width':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'amp_keycenter':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'amp_keytrack':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-96, 12)},
    'amp_veltrack':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'amp_velcurve_N':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 1)},
    'amp_random':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 24)},
    'rt_decay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 200)},
    'xf_cccurve':
        {'ver': 'v1', 'type': str,
         'validator': Choice({'gain', 'power'})},
    'xf_keycurve':
        {'ver': 'v1', 'type': str,
         'validator': Choice({'gain', 'power'})},
    'xf_velcurve':
        {'ver': 'v1', 'type': str,
         'validator': Choice({'gain', 'power'})},
    'xfin_loccN':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfin_hiccN':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfout_loccN':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfout_hiccN':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfin_lokey':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfin_hikey':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfout_lokey':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfout_hikey':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfin_lovel':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfin_hivel':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfout_lovel':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'xfout_hivel':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'eqN_bw':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0.001, 4)},
    'eqN_bwccX':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-4, 4)},
    'eqN_bw_onccX':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('eqN_bwccX')},
    'eqN_freq':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 30000)},
    'eqN_freqccX':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-30000, 30000)},
    'eqN_freq_onccX':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('eqN_freqccX')},
    'eqN_vel2freq':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-30000, 30000)},
    'eqN_gain':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-96, 24)},
    'eqN_gainccX':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-96, 24)},
    'eqN_gain_onccX':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('eqN_gainccX')},
    'eqN_vel2gain':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-96, 24)},
    'cutoff':
        {'ver': 'v1', 'type': Real,
         'validator': Min(0)},
    'cutoff_ccN':
        {'ver': 'v1', 'type': int,
         'validator': Range(-9600, 9600)},
    'cutoff_onccN':
        {'ver': 'v2', 'type': int,
         'validator': Alias('cutoff_ccN')},
    'cutoff_chanaft':
        {'ver': 'v1', 'type': int,
         'validator': Range(-9600, 9600)},
    'cutoff_polyaft':
        {'ver': 'v1', 'type': int,
         'validator': Range(-9600, 9600)},
    'fil_keytrack':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 1200)},
    'fil_keycenter':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 127)},
    'fil_random':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 9600)},
    'fil_type':
        {'ver': 'v1', 'type': str,
         'validator': Choice(
             {'lpf_1p', 'hpf_1p', 'lpf_2p', 'hpf_2p', 'bpf_2p', 'brf_2p'})},
    'fil_veltrack':
        {'ver': 'v1', 'type': int,
         'validator': Range(-9600, 9600)},
    'resonance':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 40)},
    'bend_up':
        {'ver': 'v1', 'type': int,
         'validator': Range(-9600, 9600)},
    'bend_down':
        {'ver': 'v1', 'type': int,
         'validator': Range(-9600, 9600)},
    'bend_step':
        {'ver': 'v1', 'type': int,
         'validator': Range(1, 1200)},
    'pitch_keycenter':
        {'ver': 'v1', 'type': int,
         'validator': Range(-127, 127)},
    'pitch_keytrack':
        {'ver': 'v1', 'type': int,
         'validator': Range(-1200, 1200)},
    'pitch_random':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 9600)},
    'pitch_veltrack':
        {'ver': 'v1', 'type': int,
         'validator': Range(-9600, 9600)},
    'transpose':
        {'ver': 'v1', 'type': int,
         'validator': Range(-127, 127)},
    'tune':
        {'ver': 'v1', 'type': int,
         'validator': VersionValidator(
             default=Range(-100, 100),
             aria=Range(-2400, 2400))},
    'ampeg_attack':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'ampeg_attackccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_vel2attack':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_decay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'ampeg_decayccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_vel2decay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_delay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'ampeg_delayccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_vel2delay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_hold':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'ampeg_holdccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_vel2hold':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_release':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'ampeg_releaseccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_release_onccN':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('ampeg_releaseccN')},
    'ampeg_vel2release':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_sustain':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'ampeg_sustainccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_sustain_onccN':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('ampeg_sustainccN')},
    'ampeg_vel2sustain':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_start':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'ampeg_startccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'ampeg_start_onccN':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('ampeg_startccN')},
    'fileg_attack':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'fileg_vel2attack':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'fileg_decay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'fileg_vel2decay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'fileg_delay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'fileg_vel2delay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'fileg_depth':
        {'ver': 'v1', 'type': int,
         'validator': Range(-12000, 12000)},
    'fileg_vel2depth':
        {'ver': 'v1', 'type': int,
         'validator': Range(-12000, 12000)},
    'fileg_hold':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'fileg_vel2hold':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'fileg_release':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'fileg_vel2release':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'fileg_start':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'fileg_sustain':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'fileg_vel2sustain':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'pitcheg_attack':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'pitcheg_vel2attack':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'pitcheg_decay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'pitcheg_vel2decay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'pitcheg_delay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'pitcheg_vel2delay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'pitcheg_depth':
        {'ver': 'v1', 'type': int,
         'validator': Range(-12000, 12000)},
    'pitcheg_vel2depth':
        {'ver': 'v1', 'type': int,
         'validator': Range(-12000, 12000)},
    'pitcheg_hold':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'pitcheg_vel2hold':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'pitcheg_release':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'pitcheg_vel2release':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'pitcheg_start':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'pitcheg_sustain':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'pitcheg_vel2sustain':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-100, 100)},
    'amplfo_delay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'amplfo_depth':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-10, 10)},
    'amplfo_depthccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-10, 10)},
    'amplfo_depth_onccN':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('amplfo_depthccN')},
    'amplfo_depthchanaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-10, 10)},
    'amplfo_depthpolyaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-10, 10)},
    'amplfo_fade':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'amplfo_freq':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 20)},
    'amplfo_freqccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-200, 200)},
    'amplfo_freqchanaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-200, 200)},
    'amplfo_freqpolyaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-200, 200)},
    'fillfo_delay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'fillfo_depth':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-1200, 1200)},
    'fillfo_depthccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-1200, 1200)},
    'fillfo_depth_onccN':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('fillfo_depthccN')},
    'fillfo_depthchanaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-1200, 1200)},
    'fillfo_depthpolyaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-1200, 1200)},
    'fillfo_fade':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'fillfo_freq':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 20)},
    'fillfo_freqccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-200, 200)},
    'fillfo_freqchanaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-200, 200)},
    'fillfo_freqpolyaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-200, 200)},
    'pitchlfo_delay':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'pitchlfo_depth':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-1200, 1200)},
    'pitchlfo_depthccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-1200, 1200)},
    'pitchlfo_depth_onccN':
        {'ver': 'v2', 'type': Real,
         'validator': Alias('pitchlfo_depthccN')},
    'pitchlfo_depthchanaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-1200, 1200)},
    'pitchlfo_depthpolyaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-1200, 1200)},
    'pitchlfo_fade':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 100)},
    'pitchlfo_freq':
        {'ver': 'v1', 'type': Real,
         'validator': Range(0, 20)},
    'pitchlfo_freqccN':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-200, 200)},
    'pitchlfo_freqchanaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-200, 200)},
    'pitchlfo_freqpolyaft':
        {'ver': 'v1', 'type': Real,
         'validator': Range(-200, 200)},
    'effect1':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 100)},
    'effect2':
        {'ver': 'v1', 'type': int,
         'validator': Range(0, 100)},
    'delay_samples':
        {'ver': 'v2', 'type': int,
         'validator': Any()},
    'delay_samples_onccN':
        {'ver': 'v2', 'type': int,
         'validator': Any()},
    'delay_beats':
        {'ver': 'v2', 'type': Real,
         'validator': Any()},
    'stop_beats':
        {'ver': 'v2', 'type': Real,
         'validator': Any()},
    'loop_crossfade':
        {'ver': 'v2', 'type': Real,
         'validator': Any()},
    'md5':
        {'ver': 'v2', 'type': str,
         'validator': Any()},
    'reverse_loccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 127)},
    'reverse_hiccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 127)},
    'waveguide':
        {'ver': 'v2', 'type': str,
         'validator': Choice({'on', 'off'})},
    '#define':
        {'ver': 'v2', 'type': str,
         'validator': Any()},
    'default_path':
        {'ver': 'v2', 'type': str,
         'validator': Any()},
    'note_offset':
        {'ver': 'v2', 'type': int,
         'validator': Any()},
    'octave_offset':
        {'ver': 'v2', 'type': int,
         'validator': Any()},
    'set_ccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 127)},
    'polyphony':
        {'ver': 'v2', 'type': int,
         'validator': Any()},
    'rt_dead':
        {'ver': 'v2', 'type': str,
         'validator': Choice({'on', 'off'})},
    'sustain_sw':
        {'ver': 'v2', 'type': str,
         'validator': Choice({'on', 'off'})},
    'sostenuto_sw':
        {'ver': 'v2', 'type': str,
         'validator': Choice({'on', 'off'})},
    'loprog':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 127)},
    'hiprog':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 127)},
    'lotimer':
        {'ver': 'v2', 'type': Real,
         'validator': Any()},
    'hitimer':
        {'ver': 'v2', 'type': Real,
         'validator': Any()},
    'start_loccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 127)},
    'start_hiccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 127)},
    'stop_loccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 127)},
    'stop_hiccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 127)},
    'cutoff2':
        {'ver': 'v2', 'type': Real,
         'validator': Min(0)},
    'cutoff2_onccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(-9600, 9600)},
    'cutoff2_curveccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(-9600, 9600)},
    'cutoff2_smoothccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(-9600, 9600)},
    'cutoff2_stepccN':
        {'ver': 'v2', 'type': int,
         'validator': Range(-9600, 9600)},
    'fil2_keycenter':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 127)},
    'fil2_keytrack':
        {'ver': 'v2', 'type': int,
         'validator': Range(0, 1200)},
    'fil2_type':
        {'ver': 'v2', 'type': str,
         'validator': Choice(
             {'lpf_1p', 'hpf_1p', 'lpf_2p', 'hpf_2p', 'bpf_2p', 'brf_2p',
              'bpf_1p', 'brf_1p', 'apf_1p', 'lpf_2p_sv', 'hpf_2p_sv',
              'bpf_2p_sv', 'brf_2p_sv', 'pkf_2p', 'lpf_4p', 'hpf_4p', 'lpf_6p',
              'hpf_6p', 'comb', 'pink'})},
    'fil2_veltrack':
        {'ver': 'v2', 'type': int,
         'validator': Range(-9600, 9600)},
    'resonance2':
        {'ver': 'v2', 'type': Real,
         'validator': Range(0, 40)},
    'resonance2_onccN':
        {'ver': 'v2', 'type': Real,
         'validator': Range(0, 40)},
    'resonance2_curveccN':
        {'ver': 'v2', 'type': Real,
         'validator': Range(0, 40)},
    'resonance2_smoothccN':
        {'ver': 'v2', 'type': Real,
         'validator': Range(0, 40)},
    'resonance2_stepccN':
        {'ver': 'v2', 'type': Real,
         'validator': Range(0, 40)},
    'bend_stepup':
        {'ver': 'v2', 'type': int,
         'validator': Range(1, 1200)},
    'bend_stepdown':
        {'ver': 'v2', 'type': int,
         'validator': Range(1, 1200)},
    'egN_points':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_timeX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_timeX_onccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_levelX':
        {'ver': 'v2', 'type': Real,
         'validator': Range(-1, 1)},
    'egN_levelX_onccY':
        {'ver': 'v2', 'type': Real,
         'validator': Range(-1, 1)},
    'egN_shapeX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_curveX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_sustain':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_loop':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_loop_count':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_volume':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_volume_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_amplitude':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_amplitude_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_pan':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_pan_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_width':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_width_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_pan_curve':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_pan_curveccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_freq_lfoX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_depth_lfoX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_depthadd_lfoX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_pitch':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_pitch_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_cutoff':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_cutoff_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_cutoff2':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_cutoff2_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_resonance':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_resonance_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_resonance2':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_resonance2_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_eqXfreq':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_eqXfreq_onccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_eqXbw':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_eqXbw_onccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_eqXgain':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'egN_eqXgain_onccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_freq':
        {'ver': 'v2', 'type': int,
         'validator': Any()},
    'lfoN_freq_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_freq_smoothccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_freq_stepccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_delay':
        {'ver': 'v2', 'type': Real,
         'validator': Any()},
    'lfoN_delay_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_fade':
        {'ver': 'v2', 'type': Real,
         'validator': Any()},
    'lfoN_fade_onccX':
        {'ver': 'v2', 'type': Real,
         'validator': Any()},
    'lfoN_phase':
        {'ver': 'v2', 'type': Real,
         'validator': Range(0, 1)},
    'lfoN_phase_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_count':
        {'ver': 'v2', 'type': int,
         'validator': Any()},
    'lfoN_wave':
        {'ver': 'v2', 'type': int,
         'validator': Any()},
    'lfoN_steps':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_stepX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_smooth':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_smooth_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_volume':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_volume_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_volume_smoothccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_volume_stepccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_amplitude':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_amplitude_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_amplitude_smoothccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_amplitude_stepccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_pan':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_pan_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_pan_smoothccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_pan_stepccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_width':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_width_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_width_smoothccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_width_stepccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_freq_lfoX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_depth_lfoX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_depthadd_lfoX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_pitch':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_pitch_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_pitch_smoothccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_pitch_stepccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_cutoff':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_cutoff_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_cutoff_smoothccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_cutoff_stepccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_cutoff2':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_cutoff2_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_cutoff2_smoothccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_cutoff2_stepccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_resonance':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_resonance_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_resonance_smoothccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_resonance_stepccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_resonance2':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_resonance2_onccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_resonance2_smoothccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_resonance2_stepccX':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXfreq':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXfreq_onccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXfreq_smoothccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXfreq_stepccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXbw':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXbw_onccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXbw_smoothccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXbw_stepccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXgain':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXgain_onccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXgain_smoothccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'lfoN_eqXgain_stepccY':
        {'ver': 'v2', 'type': '',
         'validator': Any()},
    'curve_index':
        {'ver': 'v2', 'type': int,
         'validator': Min(0)},
    'vN':
        {'ver': 'v2', 'type': Real,
         'validator': Range(-1, 1)},
    'direction':
        {'ver': 'aria', 'type': str,
         'validator': Choice({'forward', 'reverse'})},
    'loop_count':
        {'ver': 'aria', 'type': int,
         'validator': Any()},
    'loop_type':
        {'ver': 'aria', 'type': str,
         'validator': Choice({'forward', 'backward', 'alternate'})},
    'label_ccN':
        {'ver': 'aria', 'type': str,
         'validator': Any()},
    '#include':
        {'ver': 'aria', 'type': str,
         'validator': Any()},
    'hint_*':
        {'ver': 'aria', 'type': '',
         'validator': Any()},
    '*_mod':
        {'ver': 'aria', 'type': '',
         'validator': Any()},
    'set_hdccN':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'sostenuto_lo':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 127)},
    'sostenuto_cc':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 127)},
    'sustain_lo':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 127)},
    'sustain_cc':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 127)},
    'sw_note_offset':
        {'ver': 'aria', 'type': int,
         'validator': Any()},
    'sw_octave_offset':
        {'ver': 'aria', 'type': int,
         'validator': Any()},
    'global_label':
        {'ver': 'aria', 'type': str,
         'validator': Any()},
    'master_label':
        {'ver': 'aria', 'type': str,
         'validator': Any()},
    'group_label':
        {'ver': 'aria', 'type': str,
         'validator': Any()},
    'region_label':
        {'ver': 'aria', 'type': str,
         'validator': Any()},
    'note_polyphony':
        {'ver': 'aria', 'type': int,
         'validator': Any()},
    'note_selfmask':
        {'ver': 'aria', 'type': str,
         'validator': Choice({'on', 'off'})},
    'off_curve':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'off_shape':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'off_time':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'lohdccN':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'hihdccN':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'sw_default':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 127)},
    'sw_label':
        {'ver': 'aria', 'type': str,
         'validator': Any()},
    'sw_lolast':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 127)},
    'sw_hilast':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 127)},
    'varNN_curveccX':
        {'ver': 'aria', 'type': '',
         'validator': Any()},
    'varNN_mod':
        {'ver': 'aria', 'type': str,
         'validator': Choice({'mult', 'add'})},
    'varNN_onccX':
        {'ver': 'aria', 'type': Real,
         'validator': Range(0, 1)},
    'varNN_target':
        {'ver': 'aria', 'type': str,
         'validator': Choice({
             'amplitude', 'cutoff', 'cutoff2', 'eqNbw',
             'eqNfreq', 'eqNgain', 'pan', 'pitch',
             'resonance', 'resonance2', 'volume', 'width'})},
    'phase':
        {'ver': 'aria', 'type': str,
         'validator': Choice({'normal', 'invert'})},
    'amplitude':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 100)},
    'amplitude_onccN':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 100)},
    'amplitude_ccN':
        {'ver': 'aria', 'type': int,
         'validator': Alias('amplitude_onccN')},
    'amplitude_curveccN':
        {'ver': 'aria', 'type': '',
         'validator': Any()},
    'amplitude_smoothccN':
        {'ver': 'aria', 'type': '',
         'validator': Any()},
    'global_amplitude':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 100)},
    'master_amplitude':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 100)},
    'group_amplitude':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 100)},
    'pan_law':
        {'ver': 'aria', 'type': str,
         'validator': Choice({'mma', 'balance'})},
    'pan_keycenter':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 127)},
    'pan_keytrack':
        {'ver': 'aria', 'type': Real,
         'validator': Range(-100, 100)},
    'pan_veltrack':
        {'ver': 'aria', 'type': Real,
         'validator': Range(-100, 100)},
    'global_volume':
        {'ver': 'aria', 'type': Real,
         'validator': Range(-144, 6)},
    'master_volume':
        {'ver': 'aria', 'type': Real,
         'validator': Range(-144, 6)},
    'group_volume':
        {'ver': 'aria', 'type': Real,
         'validator': Range(-144, 6)},
    'eqN_dynamic':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 1)},
    'bend_smooth':
        {'ver': 'aria', 'type': int,
         'validator': Any()},
    'pitch':
        {'ver': 'aria', 'type': int,
         'validator': Range(-100, 100)},
    'ampeg_attack_shape':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'ampeg_decay_shape':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'ampeg_decay_zero':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 1)},
    'ampeg_dynamic':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 1)},
    'ampeg_release_shape':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'ampeg_release_zero':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 1)},
    'fileg_attack_shape':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'fileg_decay_shape':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'fileg_decay_zero':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 1)},
    'fileg_release_shape':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'fileg_release_zero':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 1)},
    'fileg_dynamic':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 1)},
    'pitcheg_attack_shape':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'pitcheg_decay_shape':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'pitcheg_decay_zero':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 1)},
    'pitcheg_release_shape':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'pitcheg_release_zero':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 1)},
    'pitcheg_dynamic':
        {'ver': 'aria', 'type': int,
         'validator': Range(0, 1)},
    'lfoN_offsetX':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'lfoN_ratio':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'lfoN_scale':
        {'ver': 'aria', 'type': Real,
         'validator': Any()},
    'lfoN_wave2':
        {'ver': 'aria', 'type': int,
         'validator': Any()},
    'param_offset':
        {'ver': 'aria', 'type': int, 'header': 'effect',
         'validator': Any()},
    'vendor_specific':
        {'ver': 'aria', 'type': str,
         'validator': Any()},
    'type':
        {'ver': 'aria', 'type': str, 'header': 'effect',
         'validator': Any()},
    'script':
        {'ver': 'linux seq', 'type': str,
         'validator': Any()},
}
