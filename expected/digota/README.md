# 1. Digota

## Summary

| Metric / Pattern | RI-1 | RI-2 | RI-3 | EI-1 | Un-1 |     | Total |
| ---------------- | ---- | ---- | ---- | ---- | ---- | --- | ----- |
| Total Warnings   | 2    | 2    | 0    | 0    | 0    |     | 4     |
| True Positives   | 2    | 2    | 0    | 0    | 0    |     | 4     |
| False Positives  | 0    | 0    | 0    | 0    | 0    |     | 0     |
| False Negatives  | 0    | 0    | 0    | 0    | 0    |     | 0     |

## RI-1: Referential Integrity - Absence of Cascading Deletes

| #   | Deleted Entity | Pending Entity | Pending Fields   | Delete Operation                                           |
| --- | -------------- | -------------- | ---------------- | ---------------------------------------------------------- |
| 1   | products       | skus           | Parent           | ProductService.Delete() → products_db.products.DeleteOne() |
| 2   | skus           | orders         | Items[\*].Parent | SkuService.Delete() → skus_db.skus.DeleteOne()             |

## RI-2: Referential Integrity - Concurrent Operations

| #   | Deleted Entity | Written Entity | Written Fields   | Delete Operation                                           | Write Operation                                   |
| --- | -------------- | -------------- | ---------------- | ---------------------------------------------------------- | ------------------------------------------------- |
| 1   | products       | skus           | Parent           | ProductService.Delete() → products_db.products.DeleteOne() | SkuService.New() → skus_db.skus.InsertOne()       |
| 2   | skus           | orders         | Items[\*].Parent | SkuService.Delete() → skus_db.skus.DeleteOne()             | OrderService.New() → orders_db.orders.InsertOne() |
