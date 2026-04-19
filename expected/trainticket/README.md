# 7. TrainTicket

## Summary

| Metric / Pattern | RI-1 | RI-2 | RI-3 | EI-1 | Un-1 |     | Total |
| ---------------- | ---- | ---- | ---- | ---- | ---- | --- | ----- |
| Total Warnings   | 14   | 17   | 4    | 0    | 0    |     | 35    |
| True Positives   | 10   | 15   | 4    | 0    | 0    |     | 29    |
| False Positives  | 4    | 2    | 0    | 0    | 0    |     | 6     |
| False Negatives  | 8    | 12   | 0    | 0    | 0    |     | 20    |

Labels:

- ✖️ (FP): False Positive due to application semantics/design
- ❌ (FP): False Positive due to incorrect foreign key caused by over-approximation in taint tracking
- 🟠 (FN): False Negative due to retrieval of related objects using values as query filters rather than as direct foreign key lookups, which further requires disabling criteria `(read_val, read_key)` for foreign key construction
- 🟡 (FN): False Negative due relationships between entities being established through user input that bridges separate RPC requests

Notes:

- TrainTicket produces 3 RI-1 false positives (✖️) where deleting contacts or price configurations does not propagate to order reservations, which is correct by design but conservatively flagged by Aletheia.

- TrainTicket produces 1 RI-1 and 2 RI-2 false positives (❌) arising from over-approximation in taint tracking. Aletheia propagates taints to all reachable variables, so when variables tainted by different database operations are combined in expressions (e.g. x←a+b), the result inherits all taints. This results in a false relationship between entities (`order_db.order.Price -> route_db.route.Distances[*]`) due to the following code in the application:

  ```go
  // BasicService -> QueryForTravel(...)
  distance := route.Distances[indexEnd] - route.Distances[indexStart]
  priceForEconomyClass := distance * int64(priceConfig.BasicPriceRate)
  ```

- TrainTicket produces 3 RI-1 and 5 RI-2 false negatives (🟠) due to retrieval of related objects using values as query filters rather than as direct foreign key lookups. For example, TrainTicket retrieves price configurations by filtering on train type instead of using a foreign key to directly access the related object. This indirection (`PriceService.FindByRouteIDAndTrainType`) prevents Aletheia from identifying relationships between entities (`price_db.price.TrainType -> train_db.train.Name`), ultimately leading to false negatives.
    
    - *Note:* To avoid incorrectly inferring inverted foreign keys (i.e., inverted `price_db.price.TrainType -> train_db.train.Name`) due to such foreign key lookup patterns, Aletheia disables the creation of references from `(read_val, read_key)` pairs during foreign key constructions. As a result, this causes the tool to miss valid relationships (`travel_db.trip.RouteID -> route_db.route.ID` and `travel_db.trip.TrainTypeName -> train_db.train.Name`) originating from regular lookups (`RouteService.GetRouteById`, `TrainService.RetrieveByName`), contributing to the number of false negatives.

- TrainTicket produces 5 RI-1 and 7 RI-2 false negatives (🟡) since relationships between entities (`delivery -> station`, `food order -> station`, `trip -> station`, and `contact -> user`) are established through user input that bridges separate RPC requests and Aletheia cannot infer them.

## Foreign Keys

| #       | Foreign Key Field                                                  | References                   |
| ------- | ------------------------------------------------------------------ | ---------------------------- |
| ❌ (FP) | order_db.order.Price                                               | route_db.route.Distances[\*] |
| 🟠 (FN) | price_db.price_config.TrainType                                    | train_db.train.Name          |
| 🟠 (FN) | travel_db.trip.RouteID                                             | route_db.route.ID            |
| 🟠 (FN) | travel_db.trip.TrainTypeName                                       | train_db.train.Name          |
| 🟡 (FN) | delivery_db.delivery.StationName                                   | station_db.station.Name      |
| 🟡 (FN) | food_order_db.food_order.StationName                               | station_db.station.Name      |
| 🟡 (FN) | trip.StartStationName, trip.StationsName, trip.TerminalStationName | station_db.station.Name      |
| 🟡 (FN) | contacts_db.contacts.AccountID                                     | user_db.user.UserID          |

## RI-1: Referential Integrity - Absence of Cascading Deletes

| #          | Deleted Entity | Pending Entity | Pending Fields                                     | Delete Operation                                                                                     |
| ---------- | -------------- | -------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 1 ✖️ (FP)  | contacts       | order          | ContactsDocumentNumber, ContactsName, DocumentType | AdminBasicInfoService.DeleteContact → ContactsService.Delete → contacts_db.contacts.DeleteOne        |
| 2 ✖️ (FP)  | contact        | order          | ContactsDocumentNumber, ContactsName, DocumentType | Dashboard.DeleteContacts → ContactsService.Delete → contacts_db.contacts.DeleteOne                   |
| 3 ✖️ (FP)  | price_config   | order          | Price                                              | AdminBasicInfoService.DeletePrice → PriceService.DeletePriceConfig → price_db.price_config.DeleteOne |
| 4          | station        | consign_record | FromPlace, ToPlace                                 | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    |
| 5          | station        | order          | FromStation, ToStation                             | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    |
| 🟡 (FN)    | station        | delivery       | StationName                                        | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    |
| 🟡 (FN)    | station        | food_order     | StationName                                        | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    |
| 🟡 (FN)    | station        | route          | EndStation, StartStation, Stations                 | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    |
| 🟡 (FN)    | station        | trip           | StartStationName, StationsName TerminalStationName | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    |
| 6          | order          | assurance      | OrderID                                            | AdminOrderService.DeleteOrder → OrderService.DeleteOrder → order_db.order.DeleteOne                  |
| 7          | order          | consign_record | OrderID, TargetDate                                | AdminOrderService.DeleteOrder → OrderService.DeleteOrder → order_db.order.DeleteOne                  |
| 8          | order          | delivery       | OrderID                                            | AdminOrderService.DeleteOrder → OrderService.DeleteOrder → order_db.order.DeleteOne                  |
| 9          | order          | food_order     | OrderID                                            | AdminOrderService.DeleteOrder → OrderService.DeleteOrder → order_db.order.DeleteOne                  |
| 10         | route          | price_config   | RouteID                                            | AdminRouteService.DeleteRoute → RouteService.DeleteRoute → route_db.route.DeleteOne                  |
| 11         | trip           | order          | Price, TrainNumber, TravelTime                     | AdminTravelService.DeleteTravel → TravelService.DeleteTrip → travel_db.trip.DeleteOne                |
| 12         | user           | consign_record | AccountID                                          | AdminUserService.DeleteUser → UserService.DeleteUser → user_db.user.DeleteOne                        |
| 13         | user           | order          | AccountID                                          | AdminUserService.DeleteUser → UserService.DeleteUser → user_db.user.DeleteOne                        |
| 🟡 (FN)    | user           | contacts       | AccountID                                          | AdminUserService.DeleteUser → UserService.DeleteUser → user_db.user.DeleteOne                        |
| 14 ❌ (FP) | route          | order          | Price                                              | AdminRouteService.DeleteRoute → RouteService.DeleteRoute → route_db.route.DeleteOne                  |
| 🟠 (FN)    | train          | price_config   | TrainType                                          | AdminBasicInfoService.DeleteTrain → TrainService.DeleteTrain → train_db.train.DeleteOne              |
| 🟠 (FN)    | train          | trip           | TrainTypeName                                      | AdminBasicInfoService.DeleteTrain → TrainService.DeleteTrain → train_db.train.DeleteOne              |
| 🟠 (FN)    | route          | trip           | RouteID                                            | AdminRouteService.DeleteRoute → RouteService.DeleteRoute → route_db.route.DeleteOne                  |

## RI-2: Referential Integrity - Concurrent Operations

| #          | Deleted Entity | Written Entity | Written Fields                                      | Delete Operation                                                                                     | Write Operation                                                                                      |
| ---------- | -------------- | -------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 1          | contacts       | order          | ContactsDocumentNumber, ContactsName, DocumentType  | AdminBasicInfoService.DeleteContact → ContactsService.Delete → contacts_db.contacts.DeleteOne        | AdminOrderService.AddOrder → OrderService.CreateNewOrder → order_db.order.InsertOne                  |
| 2          | contacts       | order          | ContactsDocumentNumber, ContactsName, DocumentType  | AdminBasicInfoService.DeleteContact → ContactsService.Delete → contacts_db.contacts.DeleteOne        | Dashboard.PreserveTicketConfirm → OrderService.CreateNewOrder → order_db.order.InsertOne             |
| 3          | contacts       | order          | ContactsDocumentNumber, ContactsName, DocumentType  | Dashboard.DeleteContacts → ContactsService.Delete → contacts_db.contacts.DeleteOne                   | AdminOrderService.AddOrder → OrderService.CreateNewOrder → order_db.order.InsertOne                  |
| 4          | contacts       | order          | ContactsDocumentNumber, ContactsName, DocumentType  | Dashboard.DeleteContacts → ContactsService.Delete → contacts_db.contacts.DeleteOne                   | Dashboard.PreserveTicketConfirm → OrderService.CreateNewOrder → order_db.order.InsertOne             |
| 5          | price_config   | order          | Price                                               | AdminBasicInfoService.DeletePrice → PriceService.DeletePriceConfig → price_db.price_config.DeleteOne | AdminOrderService.AddOrder → OrderService.CreateNewOrder → order_db.order.InsertOne                  |
| 6          | price_config   | order          | Price                                               | AdminBasicInfoService.DeletePrice → PriceService.DeletePriceConfig → price_db.price_config.DeleteOne | Dashboard.PreserveTicketConfirm → OrderService.CreateNewOrder → order_db.order.InsertOne             |
| 7          | station        | consign_record | FromPlace, ToPlace                                  | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    | Dashboard.PreserveTicketConfirm → ConsignService.InsertConsign → consign_db.consign_record.InsertOne |
| 8          | station        | order          | FromStation, ToStation                              | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    | AdminOrderService.AddOrder → OrderService.CreateNewOrder → order_db.order.InsertOne                  |
| 9          | station        | order          | FromStation, ToStation                              | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    | Dashboard.PreserveTicketConfirm → DeliveryService.Run → order_db.order.InsertOne                     |
| 🟡 (FN)    | station        | delivery       | StationName                                         | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    | Dashboard.PreserveTicketConfirm → FoodService.CreateNewFoodOrder → delivery_db.delivery.InsertOne    |
| 🟡 (FN)    | station        | food_order     | StationName                                         | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    | AdminOrderService.AddOrder → OrderService.CreateNewOrder → food_db.food_order.InsertOne              |
| 🟡 (FN)    | station        | route          | EndStation, StartStation, Stations                  | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    | AdminRouteService.AddRoute → RouteService.CreateAndModify → route_db.route.InsertOne                 |
| 🟡 (FN)    | station        | trip           | StartStationName, StationsName, TerminalStationName | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    | AdminTravelService.AddTravel → TravelService.CreateTrip → travel_db.trip.InsertOne                   |
| 🟡 (FN)    | station        | trip           | StartStationName, StationsName, TerminalStationName | AdminBasicInfoService.DeleteStation → StationService.DeleteStation → station_db.station.DeleteOne    | AdminTravelService.UpdateTravel → TravelService.UpdateTrip → travel_db.trip.InsertOne                |
| 10         | route          | price_config   | RouteID                                             | AdminRouteService.DeleteRoute → RouteService.DeleteRoute → route_db.route.DeleteOne                  | AdminBasicInfoService.AddPrice → PriceService.CreateNewPriceConfig → price_db.price_config.InsertOne |
| 11         | trip           | order          | Price, TrainNumber, TravelTime                      | AdminTravelService.DeleteTravel → TravelService.DeleteTrip → travel_db.trip.DeleteOne                | AdminOrderService.AddOrder → OrderService.CreateNewOrder → order_db.order.InsertOne                  |
| 12         | trip           | order          | Price, TrainNumber, TravelTime                      | AdminTravelService.DeleteTravel → TravelService.DeleteTrip → travel_db.trip.DeleteOne                | Dashboard.PreserveTicketConfirm → OrderService.CreateNewOrder → order_db.order.InsertOne             |
| 13         | user           | consign_record | AccountID                                           | AdminUserService.DeleteUser → UserService.DeleteUser → user_db.user.DeleteOne                        | Dashboard.PreserveTicketConfirm → ConsignService.InsertConsign → consign_db.consign_record.InsertOne |
| 14         | user           | order          | AccountID                                           | AdminUserService.DeleteUser → UserService.DeleteUser → user_db.user.DeleteOne                        | AdminOrderService.AddOrder → OrderService.CreateNewOrder → order_db.order.InsertOne                  |
| 15         | user           | order          | AccountID                                           | AdminUserService.DeleteUser → UserService.DeleteUser → user_db.user.DeleteOne                        | Dashboard.PreserveTicketConfirm → OrderService.CreateNewOrder → order_db.order.InsertOne             |
| 🟡 (FN)    | user           | contacts       | AccountID                                           | AdminUserService.DeleteUser → UserService.DeleteUser → user_db.user.DeleteOne                        | AdminBasicInfoService.AddContact → ContactsService.CreateContacts → contact_db.contact.InsertOne     |
| 🟡 (FN)    | user           | contacts       | AccountID                                           | AdminUserService.DeleteUser → UserService.DeleteUser → user_db.user.DeleteOne                        | Dashboard.AddContact → ContactsService.CreateContacts → contact_db.contact.InsertOne                 |
| 16 ❌ (FP) | route          | order          | Price                                               | AdminRouteService.DeleteRoute → RouteService.DeleteRoute → route_db.route.DeleteOne                  | AdminOrderService.AddOrder → OrderService.CreateNewOrder → order_db.order.InsertOne                  |
| 17 ❌ (FP) | route          | order          | Price                                               | AdminRouteService.DeleteRoute → RouteService.DeleteRoute → route_db.route.DeleteOne                  | Dashboard.PreserveTicketConfirm → OrderService.CreateNewOrder → order_db.order.InsertOne             |
| 🟠 (FN)    | train          | price_config   | TrainType                                           | AdminBasicInfoService.DeleteTrain → TrainService.DeleteTrain → train_db.train.DeleteOne              | AdminBasicInfoService.AddPrice → PriceService.CreateNewPriceConfig → price_db.price_config.InsertOne |
| 🟠 (FN)    | train          | trip           | TrainTypeName                                       | AdminBasicInfoService.DeleteTrain → TrainService.DeleteTrain → train_db.train.DeleteOne              | AdminTravelService.AddTravel → TravelService.CreateTrip → travel_db.trip.InsertOne                   |
| 🟠 (FN)    | train          | trip           | TrainTypeName                                       | AdminBasicInfoService.DeleteTrain → TrainService.DeleteTrain → train_db.train.DeleteOne              | AdminTravelService.UpdateTravel → TravelService.UpdateTrip → travel_db.trip.InsertOne                |
| 🟠 (FN)    | route          | trip           | RouteID                                             | AdminRouteService.DeleteRoute → RouteService.DeleteRoute → route_db.route.DeleteOne                  | AdminTravelService.AddTravel → TravelService.CreateTrip → travel_db.trip.InsertOne                   |
| 🟠 (FN)    | route          | trip           | RouteID                                             | AdminRouteService.DeleteRoute → RouteService.DeleteRoute → route_db.route.DeleteOne                  | AdminTravelService.UpdateTravel → TravelService.UpdateTrip → travel_db.trip.InsertOne                |

## RI-3: Referential Integrity - Uncoordinated Replication

| #   | Foreign Key Retrieval             | Foreign Key Usage | Constraint                                                                 | Foreign Key Retrieval Operation                                          | Foreign Key Usage Operation                        |
| --- | --------------------------------- | ----------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------- |
| 1   | assurance_db.assurance.OrderID    | order_db.order.ID | FOREIGN_KEY assurance_db.assurance.OrderID REFERENCES order_db.order.ID    | AssuranceService.FindAssuranceByOrderId → assurance_db.assurance.FindOne | OrderService.GetOrderById → order_db.order.FindOne |
| 2   | consign_db.consign_record.OrderID | order_db.order.ID | FOREIGN_KEY consign_db.consign_record.OrderID REFERENCES order_db.order.ID | ConsignService.FindByOrderId → consign_db.consign_record.FindOne         | OrderService.GetOrderById → order_db.order.FindOne |
| 3   | delivery_db.delivery.OrderID      | order_db.order.ID | FOREIGN_KEY delivery_db.delivery.OrderID REFERENCES order_db.order.ID [T]  | DeliveryService.FindDelivery → delivery_db.delivery.FindOne              | OrderService.GetOrderById → order_db.order.FindOne |
| 4   | food_db.food_order.OrderID        | order_db.order.ID | FOREIGN_KEY food_db.food_order.OrderID REFERENCES order_db.order.ID        | FoodService.FindFoodOrderByOrderId → food_db.food_order.FindOne          | OrderService.GetOrderById → order_db.order.FindOne |
