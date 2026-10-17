#include <iostream>

int main() {
    double a, b, c;

    std::cout << "Enter first number: ";
    if (!(std::cin >> a)) {
        std::cerr << "Invalid input.\n";
        return 1;
    }

    std::cout << "Enter second number: ";
    if (!(std::cin >> b)) {
        std::cerr << "Invalid input.\n";
        return 1;
    }

    std::cout << "Enter third number: ";
    if (!(std::cin >> c)) {
        std::cerr << "Invalid input.\n";
        return 1;
    }

    std::cout << "Result: " << a + b + c << '\n';
    return 0;
}
