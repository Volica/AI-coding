def solve(n, k, m):
    MOD = 10**9 + 7

    if k > n:
        return 0

    target = n - k
    dp = [0] * (target + 1)
    dp[0] = 1

    for part in range(1, k + 1):
        for total in range(part, target + 1):
            dp[total] = (dp[total] + dp[total - part]) % MOD

    factorial = 1
    for value in range(2, m + 1):
        factorial = (factorial * value) % MOD

    return (dp[target] * factorial) % MOD
