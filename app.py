from flask import Flask, render_template, request

app = Flask(__name__)


def geffe_generator(initialized):
    x1 = "00001111"
    x2 = "00110011"
    x3 = "01010101"

    x1_int = int(x1, 2)
    x2_int = int(x2, 2)
    x3_int = int(x3, 2)

    out1 = x1_int & x2_int
    out2 = x1_int ^ x3_int

    not_x1 = ~x1_int & 0xFF

    out3 = not_x1 & x3_int

    output_int = out1 ^ out3

    output_bit = bin(output_int)[2:].zfill(8)

    print("Output Bit:", output_bit)

    return output_bit


def correlation(x1, x2, x3):
    x1_int = int(x1, 2)
    x2_int = int(x2, 2)
    x3_int = int(x3, 2)

    out1 = x1_int & x2_int
    out2 = x1_int ^ x3_int

    not_x1 = ~x1_int & 0xFF

    out3 = not_x1 & x3_int

    output_int = out1 ^ out3

    output_bit = bin(output_int)[2:].zfill(8)

    return output_bit


def lfsrs_and_output(x1, x2, x3):
    x1_int = int(x1, 2)
    x2_int = int(x2, 2)
    x3_int = int(x3, 2)

    out1 = x1_int & x2_int
    out2 = x1_int ^ x3_int

    not_x1 = ~x1_int & 0xFF

    out3 = not_x1 & x3_int

    output_int = out1 ^ out3

    output_bit = bin(output_int)[2:].zfill(8)

    return output_bit


class LFSR:
    def __init__(self, state, taps):
        self.state = list(map(int, state))  # Convert string to list of integers
        self.taps = taps

    def clock(self):
        feedback_bit = sum(self.state[tap] for tap in self.taps) % 2
        self.state = [feedback_bit] + self.state[:-1]
        return self.state[-1]


class A5_1:
    def __init__(self, lfsr1_state, lfsr2_state, lfsr3_state):
        self.lfsr1 = LFSR(lfsr1_state, [5, 3, 2, 0])
        self.lfsr2 = LFSR(lfsr2_state, [5, 4])
        self.lfsr3 = LFSR(lfsr3_state, [7, 6, 5, 4])

    def clock(self):
        keystream = ""
        for _ in range(8):  # Iterate 8 times for 8 bits
            majority = (self.lfsr1.state[7] & self.lfsr2.state[7]) | (self.lfsr1.state[7] & self.lfsr3.state[7]) | (
                    self.lfsr2.state[7] & self.lfsr3.state[7])

            if self.lfsr1.state[7] == majority:
                self.lfsr1.clock()
            if self.lfsr2.state[7] == majority:
                self.lfsr2.clock()
            if self.lfsr3.state[7] == majority:
                self.lfsr3.clock()

            keystream += str(self.lfsr1.state[0] ^ self.lfsr2.state[0] ^ self.lfsr3.state[0])

        return keystream

def probability(lfsr, output):
    length = len(output)
    matches = sum(1 for c1, c2 in zip(output, lfsr) if c1 == c2)
    correlation_percentage = (matches / length) * 100
    return correlation_percentage


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    output_sequence = geffe_generator(8)  # Length is always 8
    return render_template('index.html', output_sequence=output_sequence)


@app.route('/correlation')
def correlation():
    return render_template('correlation.html')


@app.route('/correlation', methods=['POST'])
def compute_correlation():
    if request.method == 'POST':
        x1 = request.form['x1']
        x2 = request.form['x2']
        x3 = request.form['x3']

        old = {
            'x1': x1,
            'x2': x2,
            'x3': x3,
        }
        output = lfsrs_and_output(x1, x2, x3)
        # here is the second output from the second boolean function, so we can compare
        output2 = A5_1(x1, x2, x3).clock()

        correlations = {
            "x1": probability(x1, output),
            "x2": probability(x2, output),
            "x3": probability(x3, output)
        }
        correlations2 = {
            "x1": probability(x1, output2),
            "x2": probability(x2, output2),
            "x3": probability(x3, output2)
        }

        best_generator = max(correlations, key=correlations.get)
        best_generator2 = max(correlations, key=correlations2.get)

        result = {
            "output": output,
            "correlations": correlations,
            "best_generator": best_generator
        }
        result2 = {
            "output": output2,
            "correlations": correlations2,
            "best_generator": best_generator2
        }
        geffe_total_percentage = sum(correlations.values())
        a5_1_total_percentage = sum(correlations2.values())
        if geffe_total_percentage < a5_1_total_percentage:
            highlight_first = 1
        elif a5_1_total_percentage < geffe_total_percentage:
            highlight_first = 0
        else:
            # both are the same
            highlight_first = -1
        return render_template('correlation.html',
                               result=result, result2=result2,
                               highlight_first=highlight_first, old=old)
    return render_template('index.html')


def generate_possible_keys(lfsr_length, keystream_size):
    possible_keys = []
    for i in range(2 ** lfsr_length):
        possible_key = bin(i)[2:].zfill(lfsr_length)
        possible_keys.append(possible_key[:keystream_size])
    return possible_keys


@app.route('/attack')
def attack_index():
    return render_template('attack.html')


def attack(x1, x2, x3, keystream_size):
    output = lfsrs_and_output(x1, x2, x3)
    possible_keys = generate_possible_keys(len(x1), keystream_size)
    correlations = {}
    for key in possible_keys:
        correlation = probability(key, output)
        correlations[key] = correlation
    best_key = max(correlations, key=correlations.get)
    return best_key, correlations


@app.route('/attack', methods=['POST'])
def attacking():
    x1 = request.form['x1']
    x2 = request.form['x2']
    x3 = request.form['x3']
    old = {
        'x1': x1,
        'x2': x2,
        'x3': x3,
    }
    keystream_size = 8
    recovered_key, correlations = attack(x1, x2, x3, keystream_size)
    return render_template('attack.html',
                           recovered_key=recovered_key,
                           correlations=correlations,
                           old=old)


if __name__ == '__main__':
    app.run(debug=True)
