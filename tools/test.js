function() {
    var n = 0, t, i, r;
    if (this.length === 0)
        return n;
    for (t = 0,
    r = this.length; t < r; t++)
        i = this.charCodeAt(t),
        n = (n << 5) - n + i | 0;
    return n
}