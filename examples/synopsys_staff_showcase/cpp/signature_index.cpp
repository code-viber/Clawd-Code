// Optional C++17 hot-path sketch for high-volume signature indexing.
//
// Build:
//   c++ -std=c++17 -O2 -Wall -Wextra -pedantic signature_index.cpp -o signature_index
//
// Usage:
//   ./signature_index < ../sample_data/regression.log
//
// The Python demo owns the product workflow. This file shows how the same
// normalized grouping idea can be moved into a low-latency native component
// when profiling proves the parser/signature step is CPU-bound.

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <iostream>
#include <map>
#include <sstream>
#include <string>

namespace {

std::string lower_ascii(std::string input) {
  std::transform(input.begin(), input.end(), input.begin(), [](unsigned char ch) {
    return static_cast<char>(std::tolower(ch));
  });
  return input;
}

std::string compact_numbers(const std::string& input) {
  std::string output;
  bool in_number = false;

  for (char ch : input) {
    const bool is_number_char =
        std::isdigit(static_cast<unsigned char>(ch)) || ch == '.' || ch == '-';
    if (is_number_char) {
      if (!in_number) {
        output += "<num>";
        in_number = true;
      }
      continue;
    }
    in_number = false;
    output += ch;
  }

  return output;
}

std::uint64_t fnv1a(const std::string& input) {
  constexpr std::uint64_t offset = 14695981039346656037ULL;
  constexpr std::uint64_t prime = 1099511628211ULL;

  std::uint64_t hash = offset;
  for (unsigned char ch : input) {
    hash ^= ch;
    hash *= prime;
  }
  return hash;
}

std::string extract_value(const std::string& line, const std::string& key) {
  const std::string prefix = key + "=";
  const auto start = line.find(prefix);
  if (start == std::string::npos) {
    return "";
  }

  auto value_start = start + prefix.size();
  if (value_start < line.size() && line[value_start] == '"') {
    ++value_start;
    const auto end = line.find('"', value_start);
    return line.substr(value_start, end - value_start);
  }

  const auto end = line.find(' ', value_start);
  return line.substr(value_start, end - value_start);
}

}  // namespace

int main() {
  std::map<std::uint64_t, int> signature_counts;
  std::string line;

  while (std::getline(std::cin, line)) {
    if (line.empty() || line[0] == '#' || line[0] != '[') {
      continue;
    }

    const std::string tool = extract_value(line, "tool");
    const std::string code = extract_value(line, "code");
    const std::string message = extract_value(line, "message");
    if (tool.empty() || code.empty() || message.empty()) {
      continue;
    }

    const std::string normalized =
        lower_ascii(tool + "|" + code + "|" + compact_numbers(message));
    ++signature_counts[fnv1a(normalized)];
  }

  std::cout << "signature,count\n";
  for (const auto& [signature, count] : signature_counts) {
    std::cout << signature << "," << count << "\n";
  }

  return 0;
}
