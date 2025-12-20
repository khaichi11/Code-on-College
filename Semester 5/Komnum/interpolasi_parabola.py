import numpy as np

def parabolic_interpolation(f, a, b, c, tol=1e-6, max_iter=100):

    for _ in range(max_iter):
        fa, fb, fc = f(a), f(b), f(c)

        # Rumus titik minimum parabola
        numerator = (b - a)**2 * (fb - fc) - (b - c)**2 * (fb - fa)
        denominator = (b - a)*(fb - fc) - (b - c)*(fb - fa)

        if denominator == 0:
            print("Error: denominator = 0")
            return b, fb

        x_min = b - 0.5 * (numerator / denominator)
        f_min = f(x_min)

        # Update interval
        if x_min > b:
            if f_min < fb:
                a = b
                b = x_min
            else:
                c = x_min
        else:
            if f_min < fb:
                c = b
                b = x_min
            else:
                a = x_min

        # Cek konvergensi
        if abs(c - a) < tol:
            break

    return b, f(b)


# --------------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------------

def main():
    # Contoh fungsi
    def f(x):
        return (x - 1)**2

    # Titik bracketing awal
    a = 0
    b = 1
    c = 3

    xmin, ymin = parabolic_interpolation(f, a, b, c)

    print("Minimum ditemukan pada x =", xmin)
    print("Nilai minimum f(x) =", ymin)


if __name__ == "__main__":
    main()
