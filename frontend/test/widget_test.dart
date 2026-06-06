import 'package:flutter_test/flutter_test.dart';
import 'package:cardpulse/main.dart';

void main() {
  testWidgets('App renders login screen', (WidgetTester tester) async {
    await tester.pumpWidget(const CardPulseApp());
    expect(find.text('CardPulse'), findsOneWidget);
    expect(find.text('Login'), findsOneWidget);
  });
}
