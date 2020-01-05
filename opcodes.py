import re


class ValidationError(Exception):
    def __init__(self, message, value):
        self.message = message
        self.value = value


class Validator:
    def validate(self, value):
        raise NotImplementedError


class Any(Validator):
    def validate(self, value):
        pass  # every value is valid


class Min(Validator):
    def __init__(self, minimum):
        self.minimum = minimum

    def validate(self, value):
        if value < self.minimum:
            raise ValidationError(
                f'{value} less than minimum of {self.minimum}',
                value)


class Range(Validator):
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def validate(self, value):
        if not self.low < value < self.high:
            raise ValidationError(
                f'{value} not in range {self.low} to {self.high}',
                value)


def Choice(Validator):
    def __init__(self, choices):
        self.choices = choices

    def validate(self, value):
        if value not in self.choices:
            raise ValidationError(
                f'{value} not one of {self.choices}',
                value)


class OpcodeIntRepl:
    '''Converts opcodes with numeric components to their index form, and validates

    for example: 'eq3_bwcc25' -> 'eqN_bwccX'
    validates control codes in cc range.
    for example: 'eq3_bwcc256' -> ValidationError
    '''

    subs = ['N', 'X', 'Y']
    re = r'([a-z]{1,2})(\d+)'

    def __init__(self, raw_opcode):
        self.index = 0
        self.raw = raw_opcode

    def __call__(self, match):
        try:
            sub = self.subs[self.index]
        except IndexError:
            raise ValidationError(
                f'{self.raw} is not a valid opcode: unexpected number at {match.group()}',
                self.raw)
        pre, num = match.groups()
        if pre == 'cc' and int(num) > 127:
            raise ValidationError(
                f'{num} is not a valid control code',
                self.raw)
        return pre + sub


def validate_opcode_expr(raw_opcode, value):
    opcode = re.sub(OpcodeIntRepl.re, OpcodeIntRepl(), raw_opcode)
    try:
        validation = opcodes[opcode]
    except KeyError:
        raise ValidationError(
            f'{opcode} is an unknown opcode',
            raw_opcode)
    # TODO: validate value type
    validation['validator'].valdiate(value)


opcodes = {
    'count': {'type': 'integer', 'validator': Range(0, 4294967296)},
    'delay': {'type': 'float', 'validator': Range(0, 100)},
    'delay_ccN': {'type': 'float', 'validator': Range(0, 100)},
    'delay_random': {'type': 'float', 'validator': Range(0, 100)},
    'end': {'type': 'integer', 'validator': Range(0, 4294967296)},
    'loop_mode': {'type': 'string', 'validator':  Choice({'no_loop', 'one_shot', 'loop_continuous', 'loop_sustain'})},
    'loop_start': {'type': 'integer', 'validator': Range(0, 4294967296)},
    'loop_end': {'type': 'integer', 'validator': Range(0, 4294967296)},
    'offset': {'type': 'integer', 'validator': Range(0, 4294967296)},
    'offset_ccN': {'type': 'integer', 'validator': Range(0, 4294967296)},
    'offset_random': {'type': 'integer', 'validator': Range(0, 4294967296)},
    'sample': {'type': 'string', 'validator': Any()},
    'sync_beats': {'type': 'float', 'validator': Range(0, 32)},
    'sync_offset': {'type': 'float', 'validator': Range(0, 32)},
    'group': {'type': 'integer', 'validator': Range(0, 4294967296)},
    'off_by': {'type': 'integer', 'validator': Range(0, 4294967296)},
    'off_mode': {'type': 'string', 'validator':  Choice({'fast', 'normal', 'time'})},
    'output': {'type': 'integer', 'validator': Range(0, 1024)},
    'key': {'type': 'integer', 'validator': Range(0, 127)},
    'lokey': {'type': 'integer', 'validator': Range(0, 127)},
    'hikey': {'type': 'integer', 'validator': Range(0, 127)},
    'lovel': {'type': 'integer', 'validator': Range(0, 127)},
    'hivel': {'type': 'integer', 'validator': Range(0, 127)},
    'lochan': {'type': 'integer', 'validator': Range(1, 16)},
    'hichan': {'type': 'integer', 'validator': Range(1, 16)},
    'loccN': {'type': 'integer', 'validator': Range(0, 127)},
    'hiccN': {'type': 'integer', 'validator': Range(0, 127)},
    'lobend': {'type': 'integer', 'validator': Range(-8192, 8192)},
    'hibend': {'type': 'integer', 'validator': Range(-8192, 8192)},
    'sw_lokey': {'type': 'integer', 'validator': Range(0, 127)},
    'sw_hikey': {'type': 'integer', 'validator': Range(0, 127)},
    'sw_last': {'type': 'integer', 'validator': Range(0, 127)},
    'sw_down': {'type': 'integer', 'validator': Range(0, 127)},
    'sw_up': {'type': 'integer', 'validator': Range(0, 127)},
    'sw_previous': {'type': 'integer', 'validator': Range(0, 127)},
    'sw_vel': {'type': 'string', 'validator':  Choice({'current', 'previous'})},
    'lobpm': {'type': 'float', 'validator': Range(0, 500)},
    'hibpm': {'type': 'float', 'validator': Range(0, 500)},
    'lochanaft': {'type': 'integer', 'validator': Range(0, 127)},
    'hichanaft': {'type': 'integer', 'validator': Range(0, 127)},
    'lopolyaft': {'type': 'integer', 'validator': Range(0, 127)},
    'hipolyaft': {'type': 'integer', 'validator': Range(0, 127)},
    'lorand': {'type': 'float', 'validator': Range(0, 1)},
    'hirand': {'type': 'float', 'validator': Range(0, 1)},
    'seq_length': {'type': 'integer', 'validator': Range(1, 100)},
    'seq_position': {'type': 'integer', 'validator': Range(1, 100)},
    'trigger': {'type': 'string', 'validator':  Choice({'attack', 'release', 'first', 'legato', 'release_key'})},
    'on_loccN': {'type': 'integer', 'validator': Range(0, 127)},
    'on_hiccN': {'type': 'integer', 'validator': Range(0, 127)},
    'pan': {'type': 'float', 'validator': Range(-100, 100)},
    'position': {'type': 'float', 'validator': Range(-100, 100)},
    'volume': {'type': 'float', 'validator': Range(-144, 6)},
    'gain_ccN': {'type': 'float', 'validator': Range(-144, 48)},
    'width': {'type': 'float', 'validator': Range(-100, 100)},
    'amp_keycenter': {'type': 'integer', 'validator': Range(0, 127)},
    'amp_keytrack': {'type': 'float', 'validator': Range(-96, 12)},
    'amp_veltrack': {'type': 'float', 'validator': Range(-100, 100)},
    'amp_velcurve_N': {'type': 'float', 'validator': Range(0, 1)},
    'amp_random': {'type': 'float', 'validator': Range(0, 24)},
    'rt_decay': {'type': 'float', 'validator': Range(0, 200)},
    'xf_cccurve': {'type': 'string', 'validator':  Choice({'gain', 'power'})},
    'xf_keycurve': {'type': 'string', 'validator':  Choice({'gain', 'power'})},
    'xf_velcurve': {'type': 'string', 'validator':  Choice({'gain', 'power'})},
    'xfin_loccN': {'type': 'integer', 'validator': Range(0, 127)},
    'xfin_hiccN': {'type': 'integer', 'validator': Range(0, 127)},
    'xfout_loccN': {'type': 'integer', 'validator': Range(0, 127)},
    'xfout_hiccN': {'type': 'integer', 'validator': Range(0, 127)},
    'xfin_lokey': {'type': 'integer', 'validator': Range(0, 127)},
    'xfin_hikey': {'type': 'integer', 'validator': Range(0, 127)},
    'xfout_lokey': {'type': 'integer', 'validator': Range(0, 127)},
    'xfout_hikey': {'type': 'integer', 'validator': Range(0, 127)},
    'xfin_lovel': {'type': 'integer', 'validator': Range(0, 127)},
    'xfin_hivel': {'type': 'integer', 'validator': Range(0, 127)},
    'xfout_lovel': {'type': 'integer', 'validator': Range(0, 127)},
    'xfout_hivel': {'type': 'integer', 'validator': Range(0, 127)},
    'eqN_bw': {'type': 'float', 'validator': Range(0.001, 4)},
    'eqN_bwccX': {'type': 'float', 'validator': Range(-4, 4)},
    'eqN_freq': {'type': 'float', 'validator': Range(0, 30000)},
    'eqN_freqccX': {'type': 'float', 'validator': Range(-30000, 30000)},
    'eqN_vel2freq': {'type': 'float', 'validator': Range(-30000, 30000)},
    'eqN_gain': {'type': 'float', 'validator': Range(-96, 24)},
    'eqN_gainccX': {'type': 'float', 'validator': Range(-96, 24)},
    'eqN_vel2gain': {'type': 'float', 'validator': Range(-96, 24)},
    'cutoff': {'type': 'float', 'validator': Min(0)},
    'cutoff_ccN': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'cutoff_chanaft': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'cutoff_polyaft': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'fil_keytrack': {'type': 'integer', 'validator': Range(0, 1200)},
    'fil_keycenter': {'type': 'integer', 'validator': Range(0, 127)},
    'fil_random': {'type': 'integer', 'validator': Range(0, 9600)},
    'fil_type': {'type': 'string', 'validator':  Choice({'lpf_1p', 'hpf_1p', 'lpf_2p', 'hpf_2p', 'bpf_2p', 'brf_2p'})},
    'fil_veltrack': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'resonance': {'type': 'float', 'validator': Range(0, 40)},
    'bend_up': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'bend_down': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'bend_step': {'type': 'integer', 'validator': Range(1, 1200)},
    'pitch_keycenter': {'type': 'integer', 'validator': Range(-127, 127)},
    'pitch_keytrack': {'type': 'integer', 'validator': Range(-1200, 1200)},
    'pitch_random': {'type': 'integer', 'validator': Range(0, 9600)},
    'pitch_veltrack': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'transpose': {'type': 'integer', 'validator': Range(-127, 127)},
    'tune': {'type': 'integer', 'validator': Range(-100, 100)},
    'ampeg_attack': {'type': 'float', 'validator': Range(0, 100)},
    'ampeg_attackccN': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_vel2attack': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_decay': {'type': 'float', 'validator': Range(0, 100)},
    'ampeg_decayccN': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_vel2decay': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_delay': {'type': 'float', 'validator': Range(0, 100)},
    'ampeg_delayccN': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_vel2delay': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_hold': {'type': 'float', 'validator': Range(0, 100)},
    'ampeg_holdccN': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_vel2hold': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_release': {'type': 'float', 'validator': Range(0, 100)},
    'ampeg_releaseccN': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_vel2release': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_sustain': {'type': 'float', 'validator': Range(0, 100)},
    'ampeg_sustainccN': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_vel2sustain': {'type': 'float', 'validator': Range(-100, 100)},
    'ampeg_start': {'type': 'float', 'validator': Range(0, 100)},
    'ampeg_startccN': {'type': 'float', 'validator': Range(-100, 100)},
    'fileg_attack': {'type': 'float', 'validator': Range(0, 100)},
    'fileg_vel2attack': {'type': 'float', 'validator': Range(-100, 100)},
    'fileg_decay': {'type': 'float', 'validator': Range(0, 100)},
    'fileg_vel2decay': {'type': 'float', 'validator': Range(-100, 100)},
    'fileg_delay': {'type': 'float', 'validator': Range(0, 100)},
    'fileg_vel2delay': {'type': 'float', 'validator': Range(-100, 100)},
    'fileg_depth': {'type': 'integer', 'validator': Range(-12000, 12000)},
    'fileg_vel2depth': {'type': 'integer', 'validator': Range(-12000, 12000)},
    'fileg_hold': {'type': 'float', 'validator': Range(0, 100)},
    'fileg_vel2hold': {'type': 'float', 'validator': Range(-100, 100)},
    'fileg_release': {'type': 'float', 'validator': Range(0, 100)},
    'fileg_vel2release': {'type': 'float', 'validator': Range(-100, 100)},
    'fileg_start': {'type': 'float', 'validator': Range(0, 100)},
    'fileg_sustain': {'type': 'float', 'validator': Range(0, 100)},
    'fileg_vel2sustain': {'type': 'float', 'validator': Range(-100, 100)},
    'pitcheg_attack': {'type': 'float', 'validator': Range(0, 100)},
    'pitcheg_vel2attack': {'type': 'float', 'validator': Range(-100, 100)},
    'pitcheg_decay': {'type': 'float', 'validator': Range(0, 100)},
    'pitcheg_vel2decay': {'type': 'float', 'validator': Range(-100, 100)},
    'pitcheg_delay': {'type': 'float', 'validator': Range(0, 100)},
    'pitcheg_vel2delay': {'type': 'float', 'validator': Range(-100, 100)},
    'pitcheg_depth': {'type': 'integer', 'validator': Range(-12000, 12000)},
    'pitcheg_vel2depth': {'type': 'integer', 'validator': Range(-12000, 12000)},
    'pitcheg_hold': {'type': 'float', 'validator': Range(0, 100)},
    'pitcheg_vel2hold': {'type': 'float', 'validator': Range(-100, 100)},
    'pitcheg_release': {'type': 'float', 'validator': Range(0, 100)},
    'pitcheg_vel2release': {'type': 'float', 'validator': Range(-100, 100)},
    'pitcheg_start': {'type': 'float', 'validator': Range(0, 100)},
    'pitcheg_sustain': {'type': 'float', 'validator': Range(0, 100)},
    'pitcheg_vel2sustain': {'type': 'float', 'validator': Range(-100, 100)},
    'amplfo_delay': {'type': 'float', 'validator': Range(0, 100)},
    'amplfo_depth': {'type': 'float', 'validator': Range(-10, 10)},
    'amplfo_depthccN': {'type': 'float', 'validator': Range(-10, 10)},
    'amplfo_depthchanaft': {'type': 'float', 'validator': Range(-10, 10)},
    'amplfo_depthpolyaft': {'type': 'float', 'validator': Range(-10, 10)},
    'amplfo_fade': {'type': 'float', 'validator': Range(0, 100)},
    'amplfo_freq': {'type': 'float', 'validator': Range(0, 20)},
    'amplfo_freqccN': {'type': 'float', 'validator': Range(-200, 200)},
    'amplfo_freqchanaft': {'type': 'float', 'validator': Range(-200, 200)},
    'amplfo_freqpolyaft': {'type': 'float', 'validator': Range(-200, 200)},
    'fillfo_delay': {'type': 'float', 'validator': Range(0, 100)},
    'fillfo_depth': {'type': 'float', 'validator': Range(-1200, 1200)},
    'fillfo_depthccN': {'type': 'float', 'validator': Range(-1200, 1200)},
    'fillfo_depthchanaft': {'type': 'float', 'validator': Range(-1200, 1200)},
    'fillfo_depthpolyaft': {'type': 'float', 'validator': Range(-1200, 1200)},
    'fillfo_fade': {'type': 'float', 'validator': Range(0, 100)},
    'fillfo_freq': {'type': 'float', 'validator': Range(0, 20)},
    'fillfo_freqccN': {'type': 'float', 'validator': Range(-200, 200)},
    'fillfo_freqchanaft': {'type': 'float', 'validator': Range(-200, 200)},
    'fillfo_freqpolyaft': {'type': 'float', 'validator': Range(-200, 200)},
    'pitchlfo_delay': {'type': 'float', 'validator': Range(0, 100)},
    'pitchlfo_depth': {'type': 'float', 'validator': Range(-1200, 1200)},
    'pitchlfo_depthccN': {'type': 'float', 'validator': Range(-1200, 1200)},
    'pitchlfo_depthchanaft': {'type': 'float', 'validator': Range(-1200, 1200)},
    'pitchlfo_depthpolyaft': {'type': 'float', 'validator': Range(-1200, 1200)},
    'pitchlfo_fade': {'type': 'float', 'validator': Range(0, 100)},
    'pitchlfo_freq': {'type': 'float', 'validator': Range(0, 20)},
    'pitchlfo_freqccN': {'type': 'float', 'validator': Range(-200, 200)},
    'pitchlfo_freqchanaft': {'type': 'float', 'validator': Range(-200, 200)},
    'pitchlfo_freqpolyaft': {'type': 'float', 'validator': Range(-200, 200)},
    'effect1': {'type': 'integer', 'validator': Range(0, 100)},
    'effect2': {'type': 'integer', 'validator': Range(0, 100)},
    'delay_samples': {'type': 'integer', 'validator': Any()},
    'delay_samples_onccN': {'type': 'integer', 'validator': Any()},
    'delay_beats': {'type': 'float', 'validator': Any()},
    'stop_beats': {'type': 'float', 'validator': Any()},
    'loop_crossfade': {'type': 'float', 'validator': Any()},
    'md5': {'type': 'string', 'validator': Any()},
    'reverse_loccN': {'type': 'integer', 'validator': Range(0, 127)},
    'reverse_hiccN': {'type': 'integer', 'validator': Range(0, 127)},
    'waveguide': {'type': 'string', 'validator':  Choice({'on', 'off'})},
    '#define': {'type': 'string', 'validator': Any()},
    'default_path': {'type': 'string', 'validator': Any()},
    'note_offset': {'type': 'integer', 'validator': Any()},
    'octave_offset': {'type': 'integer', 'validator': Any()},
    'set_ccN': {'type': 'integer', 'validator': Range(0, 127)},
    'polyphony': {'type': 'integer', 'validator': Any()},
    'rt_dead': {'type': 'string', 'validator':  Choice({'on', 'off'})},
    'sustain_sw': {'type': 'string', 'validator':  Choice({'on', 'off'})},
    'sostenuto_sw': {'type': 'string', 'validator':  Choice({'on', 'off'})},
    'loprog': {'type': 'integer', 'validator': Range(0, 127)},
    'hiprog': {'type': 'integer', 'validator': Range(0, 127)},
    'lotimer': {'type': 'float', 'validator': Any()},
    'hitimer': {'type': 'float', 'validator': Any()},
    'start_loccN': {'type': 'integer', 'validator': Range(0, 127)},
    'start_hiccN': {'type': 'integer', 'validator': Range(0, 127)},
    'stop_loccN': {'type': 'integer', 'validator': Range(0, 127)},
    'stop_hiccN': {'type': 'integer', 'validator': Range(0, 127)},
    'cutoff2': {'type': 'float', 'validator': Min(0)},
    'cutoff2_onccN': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'cutoff2_curveccN': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'cutoff2_smoothccN': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'cutoff2_stepccN': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'fil2_keycenter': {'type': 'integer', 'validator': Range(0, 127)},
    'fil2_keytrack': {'type': 'integer', 'validator': Range(0, 1200)},
    'fil2_type': {'type': 'string', 'validator':  Choice({'lpf_1p', 'hpf_1p', 'lpf_2p', 'hpf_2p', 'bpf_2p', 'brf_2p', 'bpf_1p', 'brf_1p', 'apf_1p', 'lpf_2p_sv', 'hpf_2p_sv', 'bpf_2p_sv', 'brf_2p_sv', 'pkf_2p', 'lpf_4p', 'hpf_4p', 'lpf_6p', 'hpf_6p', 'comb', 'pink'})},
    'fil2_veltrack': {'type': 'integer', 'validator': Range(-9600, 9600)},
    'resonance2': {'type': 'float', 'validator': Range(0, 40)},
    'resonance2_onccN': {'type': 'float', 'validator': Range(0, 40)},
    'resonance2_curveccN': {'type': 'float', 'validator': Range(0, 40)},
    'resonance2_smoothccN': {'type': 'float', 'validator': Range(0, 40)},
    'resonance2_stepccN': {'type': 'float', 'validator': Range(0, 40)},
    'bend_stepup': {'type': 'integer', 'validator': Range(1, 1200)},
    'bend_stepdown': {'type': 'integer', 'validator': Range(1, 1200)},
    'egN_points': {'type': '', 'validator': Any()},
    'egN_timeX': {'type': '', 'validator': Any()},
    'egN_timeX_onccY': {'type': '', 'validator': Any()},
    'egN_levelX': {'type': 'float', 'validator': Range(-1, 1)},
    'egN_levelX_onccY': {'type': 'float', 'validator': Range(-1, 1)},
    'egN_shapeX': {'type': '', 'validator': Any()},
    'egN_curveX': {'type': '', 'validator': Any()},
    'egN_sustain': {'type': '', 'validator': Any()},
    'egN_loop': {'type': '', 'validator': Any()},
    'egN_loop_count': {'type': '', 'validator': Any()},
    'egN_volume': {'type': '', 'validator': Any()},
    'egN_volume_onccX': {'type': '', 'validator': Any()},
    'egN_amplitude': {'type': '', 'validator': Any()},
    'egN_amplitude_onccX': {'type': '', 'validator': Any()},
    'egN_pan': {'type': '', 'validator': Any()},
    'egN_pan_onccX': {'type': '', 'validator': Any()},
    'egN_width': {'type': '', 'validator': Any()},
    'egN_width_onccX': {'type': '', 'validator': Any()},
    'egN_pan_curve': {'type': '', 'validator': Any()},
    'egN_pan_curveccX': {'type': '', 'validator': Any()},
    'egN_freq_lfoX': {'type': '', 'validator': Any()},
    'egN_depth_lfoX': {'type': '', 'validator': Any()},
    'egN_depthadd_lfoX': {'type': '', 'validator': Any()},
    'egN_pitch': {'type': '', 'validator': Any()},
    'egN_pitch_onccX': {'type': '', 'validator': Any()},
    'egN_cutoff': {'type': '', 'validator': Any()},
    'egN_cutoff_onccX': {'type': '', 'validator': Any()},
    'egN_cutoff2': {'type': '', 'validator': Any()},
    'egN_cutoff2_onccX': {'type': '', 'validator': Any()},
    'egN_resonance': {'type': '', 'validator': Any()},
    'egN_resonance_onccX': {'type': '', 'validator': Any()},
    'egN_resonance2': {'type': '', 'validator': Any()},
    'egN_resonance2_onccX': {'type': '', 'validator': Any()},
    'egN_eqXfreq': {'type': '', 'validator': Any()},
    'egN_eqXfreq_onccY': {'type': '', 'validator': Any()},
    'egN_eqXbw': {'type': '', 'validator': Any()},
    'egN_eqXbw_onccY': {'type': '', 'validator': Any()},
    'egN_eqXgain': {'type': '', 'validator': Any()},
    'egN_eqXgain_onccY': {'type': '', 'validator': Any()},
    'lfoN_freq': {'type': 'integer', 'validator': Any()},
    'lfoN_freq_onccX': {'type': '', 'validator': Any()},
    'lfoN_freq_smoothccX': {'type': '', 'validator': Any()},
    'lfoN_freq_stepccX': {'type': '', 'validator': Any()},
    'lfoN_delay': {'type': 'float', 'validator': Any()},
    'lfoN_delay_onccX': {'type': '', 'validator': Any()},
    'lfoN_fade': {'type': 'float', 'validator': Any()},
    'lfoN_fade_onccX': {'type': 'float', 'validator': Any()},
    'lfoN_phase': {'type': 'float', 'validator': Range(0, 1)},
    'lfoN_phase_onccX': {'type': '', 'validator': Any()},
    'lfoN_count': {'type': 'integer', 'validator': Any()},
    'lfoN_wave': {'type': 'integer', 'validator': Any()},
    'lfoN_steps': {'type': '', 'validator': Any()},
    'lfoN_stepX': {'type': '', 'validator': Any()},
    'lfoN_smooth': {'type': '', 'validator': Any()},
    'lfoN_smooth_onccX': {'type': '', 'validator': Any()},
    'lfoN_volume': {'type': '', 'validator': Any()},
    'lfoN_volume_onccX': {'type': '', 'validator': Any()},
    'lfoN_volume_smoothccX': {'type': '', 'validator': Any()},
    'lfoN_volume_stepccX': {'type': '', 'validator': Any()},
    'lfoN_amplitude': {'type': '', 'validator': Any()},
    'lfoN_amplitude_onccX': {'type': '', 'validator': Any()},
    'lfoN_amplitude_smoothccX': {'type': '', 'validator': Any()},
    'lfoN_amplitude_stepccX': {'type': '', 'validator': Any()},
    'lfoN_pan': {'type': '', 'validator': Any()},
    'lfoN_pan_onccX': {'type': '', 'validator': Any()},
    'lfoN_pan_smoothccX': {'type': '', 'validator': Any()},
    'lfoN_pan_stepccX': {'type': '', 'validator': Any()},
    'lfoN_width': {'type': '', 'validator': Any()},
    'lfoN_width_onccX': {'type': '', 'validator': Any()},
    'lfoN_width_smoothccX': {'type': '', 'validator': Any()},
    'lfoN_width_stepccX': {'type': '', 'validator': Any()},
    'lfoN_freq_lfoX': {'type': '', 'validator': Any()},
    'lfoN_depth_lfoX': {'type': '', 'validator': Any()},
    'lfoN_depthadd_lfoX': {'type': '', 'validator': Any()},
    'lfoN_pitch': {'type': '', 'validator': Any()},
    'lfoN_pitch_onccX': {'type': '', 'validator': Any()},
    'lfoN_pitch_smoothccX': {'type': '', 'validator': Any()},
    'lfoN_pitch_stepccX': {'type': '', 'validator': Any()},
    'lfoN_cutoff': {'type': '', 'validator': Any()},
    'lfoN_cutoff_onccX': {'type': '', 'validator': Any()},
    'lfoN_cutoff_smoothccX': {'type': '', 'validator': Any()},
    'lfoN_cutoff_stepccX': {'type': '', 'validator': Any()},
    'lfoN_cutoff2': {'type': '', 'validator': Any()},
    'lfoN_cutoff2_onccX': {'type': '', 'validator': Any()},
    'lfoN_cutoff2_smoothccX': {'type': '', 'validator': Any()},
    'lfoN_cutoff2_stepccX': {'type': '', 'validator': Any()},
    'lfoN_resonance': {'type': '', 'validator': Any()},
    'lfoN_resonance_onccX': {'type': '', 'validator': Any()},
    'lfoN_resonance_smoothccX': {'type': '', 'validator': Any()},
    'lfoN_resonance_stepccX': {'type': '', 'validator': Any()},
    'lfoN_resonance2': {'type': '', 'validator': Any()},
    'lfoN_resonance2_onccX': {'type': '', 'validator': Any()},
    'lfoN_resonance2_smoothccX': {'type': '', 'validator': Any()},
    'lfoN_resonance2_stepccX': {'type': '', 'validator': Any()},
    'lfoN_eqXfreq': {'type': '', 'validator': Any()},
    'lfoN_eqXfreq_onccY': {'type': '', 'validator': Any()},
    'lfoN_eqXfreq_smoothccY': {'type': '', 'validator': Any()},
    'lfoN_eqXfreq_stepccY': {'type': '', 'validator': Any()},
    'lfoN_eqXbw': {'type': '', 'validator': Any()},
    'lfoN_eqXbw_onccY': {'type': '', 'validator': Any()},
    'lfoN_eqXbw_smoothccY': {'type': '', 'validator': Any()},
    'lfoN_eqXbw_stepccY': {'type': '', 'validator': Any()},
    'lfoN_eqXgain': {'type': '', 'validator': Any()},
    'lfoN_eqXgain_onccY': {'type': '', 'validator': Any()},
    'lfoN_eqXgain_smoothccY': {'type': '', 'validator': Any()},
    'lfoN_eqXgain_stepccY': {'type': '', 'validator': Any()},
    'curve_index': {'type': 'integer', 'validator': Min(0)},
    'vN': {'type': 'float', 'validator': Range(-1, 1)},
}
