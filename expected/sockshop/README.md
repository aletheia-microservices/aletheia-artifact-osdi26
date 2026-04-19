# 5. SockShop

## Summary

| Metric / Pattern | RI-1 | RI-2 | RI-3 | EI-1 | Un-1 |     | Total |
| ---------------- | ---- | ---- | ---- | ---- | ---- | --- | ----- |
| Total Warnings   | 3    | 3    | 0    | 0    | 0    |     | 6     |
| True Positives   | 0    | 0    | 0    | 0    | 0    |     | 0     |
| False Positives  | 3    | 3    | 0    | 0    | 0    |     | 6     |
| False Negatives  | 0    | 0    | 0    | 0    | 0    |     | 0     |

Labels:

- ✖️ (FP): False Positive due to application semantics

Notes:

- SockShop produces 3 RI-1 false positives from cart deletions that intentionally do not cascade to orders, and 3 RI-2 false positives from concurrent cart deletions and order creation where the application coordinates safely.

## RI-1: Referential Integrity - Absence of Cascading Deletes

| #         | Deleted Entity | Pending Entity | Pending Fields | Delete Operation                                                              |
| --------- | -------------- | -------------- | -------------- | ----------------------------------------------------------------------------- |
| 1 ✖️ (FP) | carts          | orders         | Items          | Frontend.DeleteCart() → CartService.DeleteCart() → cart_db.carts.DeleteMany() |
| 2 ✖️ (FP) | carts          | orders         | Items          | Frontend.Login() → CartService.MergeCarts() → cart_db.carts.DeleteOne()       |
| 3 ✖️ (FP) | carts          | orders         | Items          | Frontend.Register() → CartService.MergeCarts() → cart_db.carts.DeleteOne()    |

## RI-2: Referential Integrity - Concurrent Operations

| #         | Deleted Entity | Written Entity | Written Fields | Delete Operation                                                              | Write Operation                                                             |
| --------- | -------------- | -------------- | -------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 1 ✖️ (FP) | carts          | orders         | Items          | Frontend.DeleteCart() → CartService.DeleteCart() → cart_db.carts.DeleteMany() | Frontend.NewOrder() → OrderService.NewOrder() → order_db.orders.InsertOne() |
| 2 ✖️ (FP) | carts          | orders         | Items          | Frontend.Login() → CartService.MergeCarts() → cart_db.carts.DeleteOne()       | Frontend.NewOrder() → OrderService.NewOrder() → order_db.orders.InsertOne() |
| 3 ✖️ (FP) | carts          | orders         | Items          | Frontend.Register() → CartService.MergeCarts() → cart_db.carts.DeleteOne()    | Frontend.NewOrder() → OrderService.NewOrder() → order_db.orders.InsertOne() |
