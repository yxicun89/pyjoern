import java.io.PrintStream;
import java.util.List;
import java.util.ArrayList;

public class DataProcessor {

    public static int processData(List<String> dataList) {
        if (dataList == null || dataList.isEmpty()) {
            System.out.println("List is empty.");
            return 0;
        }

        int total = 0;
        for (String item : dataList) {
            try {
                int value = Integer.parseInt(item);
                if (value % 2 == 0) {
                    System.out.println(value + " is even.");
                    total += value;
                } else {
                    System.out.println(value + " is odd.");
                }
            } catch (NumberFormatException e) {
                // 'four' のような無効な文字列を処理する
                System.err.println("Skipping invalid item: " + item);
                continue; // Javaのcontinueと同様
            }
        }

        System.out.println("Processing complete.");
        return total;
    }

    public static void main(String[] args) {
        List<String> numbers = new ArrayList<>();
        numbers.add("1");
        numbers.add("2");
        numbers.add("3");
        numbers.add("four");
        numbers.add("5");
        numbers.add("6");

        int result = processData(numbers);
        System.out.println("Total sum of even numbers: " + result);
    }
}
