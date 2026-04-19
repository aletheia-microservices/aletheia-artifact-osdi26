# 2. EShopMicroservices

## Summary

| Metric / Pattern | RI-1 | RI-2 | RI-3 | EI-1 | Un-1 |     | Total |
| ---------------- | ---- | ---- | ---- | ---- | ---- | --- | ----- |
| Total Warnings   | 2    | 6    | 0    | 0    | 0    |     | 8     |
| True Positives   | 2    | 6    | 0    | 0    | 0    |     | 8     |
| False Positives  | 0    | 0    | 0    | 0    | 0    |     | 0     |
| False Negatives  | 1    | 1    | 0    | 0    | 0    |     | 2     |

Labels:

- 🟡 (FN): False Negative

Notes:

- EShopMicroservices produces 1 RI-1 and 1 RI-2 false negatives since relationships between entities `product` and `discount` are established through user input that bridges separate RPC requests and Aletheia cannot infer them.

## Foreign Keys

| #       | Foreign Key Field                | References              |
| ------- | -------------------------------- | ----------------------- |
| 🟡 (FN) | discount_db.discount.ProductName | catalog_db.product.Name |

## RI-1: Referential Integrity - Absence of Cascading Deletes

| #       | Deleted Entity | Pending Entity | Pending Fields                                                         | Delete Operation                                                  |
| ------- | -------------- | -------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------- |
| 1       | product        | basket         | Items[\*], Items[\*].Price, Items[\*].ProductId, Items[\*].ProductName | CatalogService.DeleteProduct() → catalog_db.product.DeleteOne()   |
| 2       | discount       | basket         | Items[\*].ProductName                                                  | DiscountService.DeleteDiscount() → discount_db.coupon.DeleteOne() |
| 🟡 (FN) | product        | discount       | ProductName                                                            | CatalogService.DeleteProduct() → catalog_db.product.DeleteOne()   |

## RI-2: Referential Integrity - Concurrent Operations

| #       | Deleted Entity | Written Entity | Written Fields                                                         | Delete Operation                                                  | Write Operation                                                   |
| ------- | -------------- | -------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------- |
| 1       | product        | basket         | Items[\*], Items[\*].Price, Items[\*].ProductId, Items[\*].ProductName | CatalogService.DeleteProduct() → catalog_db.product.DeleteOne()   | BasketService.StoreBasket() → basket_db.basket.InsertOne()        |
| 2       | product        | basket         | Items[\*], Items[\*].Price, Items[\*].ProductId, Items[\*].ProductName | CatalogService.DeleteProduct() → catalog_db.product.DeleteOne()   | WebApp.OnPostAddToCartAsync() → basket_db.basket.InsertOne()      |
| 3       | product        | basket         | Items[\*], Items[\*].Price, Items[\*].ProductId, Items[\*].ProductName | CatalogService.DeleteProduct() → catalog_db.product.DeleteOne()   | WebApp.OnPostRemoveToCartAsync() → basket_db.basket.InsertOne()   |
| 4       | discount       | basket         | Items[\*].ProductName                                                  | DiscountService.DeleteDiscount() → discount_db.coupon.DeleteOne() | BasketService.StoreBasket() → basket_db.basket.InsertOne()        |
| 5       | discount       | basket         | Items[\*].ProductName                                                  | DiscountService.DeleteDiscount() → discount_db.coupon.DeleteOne() | WebApp.OnPostAddToCartAsync() → basket_db.basket.InsertOne()      |
| 6       | discount       | basket         | Items[\*].ProductName                                                  | DiscountService.DeleteDiscount() → discount_db.coupon.DeleteOne() | WebApp.OnPostRemoveToCartAsync() → basket_db.basket.InsertOne()   |
| 🟡 (FN) | product        | discount       | ProductName                                                            | CatalogService.DeleteProduct() → catalog_db.product.DeleteOne()   | DiscountService.CreateDiscount() → discount_db.coupon.InsertOne() |
