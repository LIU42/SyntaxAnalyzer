from grammars import Token
from analyzer import SyntaxAnalyzer


def syntax_analysis(analyzer, source_path, output_path):
    with open(source_path, 'r') as sources:
        errors = analyzer.analysis(Token.loads(sources.readlines()))

    with open(output_path, 'w') as outputs:
        outputs.writelines(f'{error}\n' for error in errors)


def main():
    analyzer = SyntaxAnalyzer()
    syntax_analysis(analyzer, 'samples/sample1.txt', 'outputs/output1.txt')
    syntax_analysis(analyzer, 'samples/sample2.txt', 'outputs/output2.txt')
    syntax_analysis(analyzer, 'samples/sample3.txt', 'outputs/output3.txt')
    syntax_analysis(analyzer, 'samples/sample4.txt', 'outputs/output4.txt')


if __name__ == '__main__':
    main()
