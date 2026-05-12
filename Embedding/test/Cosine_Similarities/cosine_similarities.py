import numpy as np
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA

# ── 1. SENTENCES ──────────────────────────────────────────────────────────────
# Grouped intentionally: refund, tech support, food
# Watch how similar groups cluster together

sentences = [
    # Refund group
    "I want a refund for my order",
    "How do I get my money back?",
    "Can I return this product?",

    # Tech support group
    "My laptop won't turn on",
    "The screen is completely black",
    "I'm having trouble with my device",

    # Food group
    "This pizza is absolutely delicious",
    "I love Italian cuisine",
    "The pasta was incredible",
]

labels = [
    "refund-1", "refund-2", "refund-3",
    "tech-1",   "tech-2",   "tech-3",
    "food-1",   "food-2",   "food-3",
]

# ── 2. EMBED ──────────────────────────────────────────────────────────────────
print("Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")  # downloads ~80MB first run

print("Generating embeddings...")
embeddings = model.encode(sentences)  # shape: (9, 384)

print(f"Embedding shape: {embeddings.shape}")  # (9, 384) — 9 sentences, 384 dims each

# ── 3. COSINE SIMILARITY (manual numpy — no sklearn shortcuts) ────────────────
def cosine_similarity(a, b):
    dot_product = np.dot(a, b)
    magnitude_a = np.linalg.norm(a)
    magnitude_b = np.linalg.norm(b)
    return dot_product / (magnitude_a * magnitude_b)

# Build full similarity matrix
n = len(sentences)
sim_matrix = np.zeros((n, n))

for i in range(n):
    for j in range(n):
        sim_matrix[i][j] = cosine_similarity(embeddings[i], embeddings[j])

# ── 4. PRINT SIMILARITY MATRIX ────────────────────────────────────────────────
print("\n── Similarity Matrix ──")
print(f"{'':12}", end="")
for label in labels:
    print(f"{label:10}", end="")
print()

for i, label in enumerate(labels):
    print(f"{label:12}", end="")
    for j in range(n):
        score = sim_matrix[i][j]
        print(f"{score:<10.2f}", end="")
    print()

# ── 5. SPOT CHECK — print most interesting pairs ──────────────────────────────
print("\n── Spot Checks ──")
pairs = [
    (0, 1, "refund vs money back"),
    (0, 2, "refund vs return product"),
    (0, 3, "refund vs laptop won't turn on"),
    (0, 6, "refund vs pizza"),
    (3, 4, "laptop vs black screen"),
    (6, 7, "pizza vs Italian cuisine"),
]

for i, j, desc in pairs:
    score = cosine_similarity(embeddings[i], embeddings[j])
    print(f"{desc:40} -> {score:.4f}")

# ── 6. PCA VISUALIZATION ──────────────────────────────────────────────────────
print("\nGenerating PCA visualization...")

pca = PCA(n_components=2)
reduced = pca.fit_transform(embeddings)  # compress 384 dims -> 2 dims

colors = ["#e74c3c"] * 3 + ["#3498db"] * 3 + ["#2ecc71"] * 3  # red, blue, green

plt.figure(figsize=(10, 7))
plt.title("Sentence Embeddings — PCA to 2D\n(similar meanings should cluster)", fontsize=13)

for i, (x, y) in enumerate(reduced):
    plt.scatter(x, y, color=colors[i], s=120, zorder=2)
    plt.annotate(
        labels[i],
        (x, y),
        textcoords="offset points",
        xytext=(8, 4),
        fontsize=10,
    )

# Draw lines within each group to make clusters obvious
groups = [(0, 1, 2, "#e74c3c"), (3, 4, 5, "#3498db"), (6, 7, 8, "#2ecc71")]
for i, j, k, color in groups:
    for a, b in [(i, j), (j, k), (i, k)]:
        plt.plot(
            [reduced[a][0], reduced[b][0]],
            [reduced[a][1], reduced[b][1]],
            color=color, alpha=0.3, linewidth=1.5
        )

plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("embeddings_pca.png", dpi=150)
plt.show()
print("Saved to embeddings_pca.png")