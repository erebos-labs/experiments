// Independent exact even-subgraph sum. No third party libraries.
// All ice vertices are counted by a local Fourier identity; see DERIVATION.md.
#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using U128 = unsigned __int128;
using Bits = std::uint64_t;

std::string decimal(U128 x) {
    if (!x) return "0";
    std::string s;
    while (x) { s.push_back('0' + x % 10); x /= 10; }
    std::reverse(s.begin(), s.end());
    return s;
}

void count_loops(int n, bool periodic) {
    const int vertices = n * n;
    // Toroidal n<=5 uses <=50 edges; open n<=6 uses <=60.
    const int hcount = periodic ? vertices : n * (n - 1);
    const int edges = 2 * hcount;
    if (edges > 64 || (periodic && n > 5) || (!periodic && n > 6))
        throw std::runtime_error("bounded loop enumeration exceeded");
    std::vector<Bits> incident(vertices, 0), basis;
    auto h = [&](int r, int c) { return r * (periodic ? n : n - 1) + c; };
    auto v = [&](int r, int c) { return hcount + r * n + c; };
    auto add_edge = [&](int edge, int a, int b) {
        incident[a] |= Bits(1) << edge;
        incident[b] |= Bits(1) << edge;
    };
    for (int r = 0; r < n; ++r)
        for (int c = 0; c < n; ++c) {
            if (periodic || c < n - 1)
                add_edge(h(r, c), r * n + c, r * n + (c + 1) % n);
            if (periodic || r < n - 1)
                add_edge(v(r, c), r * n + c, ((r + 1) % n) * n + c);
        }
    const int faces = periodic ? n : n - 1;
    for (int r = 0; r < faces; ++r)
        for (int c = 0; c < faces; ++c) {
            if (periodic && r == n - 1 && c == n - 1) continue;
            basis.push_back((Bits(1) << h(r, c)) |
                            (Bits(1) << v(r, (c + 1) % n)) |
                            (Bits(1) << h((r + 1) % n, c)) |
                            (Bits(1) << v(r, c)));
        }
    if (periodic) {
        Bits horizontal = 0, vertical = 0;
        for (int i = 0; i < n; ++i) {
            horizontal |= Bits(1) << h(0, i);
            vertical |= Bits(1) << v(i, 0);
        }
        basis.push_back(horizontal);
        basis.push_back(vertical);
    }
    const int rank = edges - vertices + 1;
    if (int(basis.size()) != rank) throw std::runtime_error("basis count");
    // Verify linear independence over GF(2), separately from enumeration.
    std::array<Bits, 64> pivots{};
    for (Bits cycle : basis) {
        Bits x = cycle;
        while (x) {
            int k = 63 - std::countl_zero(x);
            if (pivots[k]) x ^= pivots[k];
            else { pivots[k] = x; break; }
        }
        if (!x) throw std::runtime_error("dependent cycle basis");
        for (Bits mask : incident)
            if (std::popcount(cycle & mask) % 2) throw std::runtime_error("not a cycle");
    }
    std::vector<std::vector<int>> affected;
    for (Bits cycle : basis) {
        affected.emplace_back();
        for (int j = 0; j < vertices; ++j)
            if (cycle & incident[j]) affected.back().push_back(j);
    }
    std::vector<U128> powers(vertices + 1, 1), histogram(vertices + 1, 0);
    for (int i = 1; i <= vertices; ++i) powers[i] = powers[i - 1] * 3;
    const auto start = std::chrono::steady_clock::now();
    Bits selected = 0;
    int degree_two = 0;
    U128 weighted = powers[vertices];
    histogram[0] = 1;
    const Bits terms = Bits(1) << rank;
    for (Bits i = 1; i < terms; ++i) {
        int j = std::countr_zero(i); // binary-reflected Gray-code update
        for (int vertex : affected[j])
            degree_two -= std::popcount(selected & incident[vertex]) == 2;
        selected ^= basis[j];
        for (int vertex : affected[j])
            degree_two += std::popcount(selected & incident[vertex]) == 2;
        weighted += powers[vertices - degree_two];
        histogram[degree_two] += 1;
    }
    U128 numerator = weighted;
    U128 denominator = 1;
    const int exponent = (periodic ? 0 : 2 * n) - vertices;
    if (exponent >= 0) numerator <<= exponent;
    else denominator <<= -exponent;
    if (numerator % denominator) throw std::runtime_error("nonintegral ice count");
    const auto seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    std::cout << "{\"n\":" << n << ",\"boundary\":\"" << (periodic ? "torus" : "free")
              << "\",\"cycle_rank\":" << rank << ",\"subgraphs\":" << terms
              << ",\"weighted_numerator\":\"" << decimal(weighted)
              << "\",\"ice_count\":\"" << decimal(numerator / denominator)
              << "\",\"seconds\":" << seconds << ",\"degree_two_histogram\":[";
    for (int i = 0; i <= vertices; ++i) {
        if (i) std::cout << ',';
        std::cout << '"' << decimal(histogram[i]) << '"';
    }
    std::cout << "]}" << std::endl;
}

int main() {
    for (int n = 2; n <= 5; ++n) count_loops(n, true);
    for (int n = 2; n <= 6; ++n) count_loops(n, false);
}
