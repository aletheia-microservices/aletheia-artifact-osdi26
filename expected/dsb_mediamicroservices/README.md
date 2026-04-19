# 4. MediaMicroservices

## Summary

| Metric / Pattern | RI-1 | RI-2 | RI-3 | EI-1 | Un-1 |     | Total |
| ---------------- | ---- | ---- | ---- | ---- | ---- | --- | ----- |
| Total Warnings   | 0    | 0    | 3    | 1    | 1    |     | 5     |
| True Positives   | 0    | 0    | 3    | 1    | 1    |     | 5     |
| False Positives  | 0    | 0    | 0    | 0    | 0    |     | 0     |
| False Negatives  | 0    | 0    | 0    | 0    | 0    |     | 0     |

## RI-3: Referential Integrity - Uncoordinated Replication

| #   | Foreign Key Retrieval                             | Foreign Key Usage                 | Constraint                                                                                                 | Foreign Key Retrieval Operation                                            | Foreign Key Usage Operation                                          |
| --- | ------------------------------------------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| 1   | movie_info_db.movie_info.Casts[\*].CastInfoID     | cast_info_db.cast.CastInfoID      | FOREIGN_KEY movie_info_db.movie_info.Casts[\*].CastInfoID REFERENCES cast_info_db.cast.CastInfoID          | MovieInfoService.ReadMovieInfo → movie_info_db.movie_info.FindOne          | CastInfoService.ReadCastInfos → cast_info_db.cast.FindMany           |
| 2   | movie_info_db.movie_info.PlotID                   | plot_db.plot.PlotID               | FOREIGN_KEY movie_info_db.movie_info.PlotID REFERENCES plot_db.plot.PlotID                                 | MovieInfoService.ReadMovieInfo → movie_info_db.movie_info.FindOne          | PlotService.ReadPlot → plot_db.plot.FindOne                          |
| 3   | movie_review_db.movie_review.Reviews[\*].ReviewID | review_storage_db.review.ReviewID | FOREIGN_KEY movie_review_db.movie_review.Reviews[\*].ReviewID REFERENCES review_storage_db.review.ReviewID | MovieReviewService.ReadMovieReviews → movie_review_db.movie_review.FindOne | ReviewStorageService.ReadReviews → review_storage_db.review.FindMany |

## EI-1: Entity Integrity - Uncoordinated Replication

| #   | Primary Key Field 1              | Primary Key Field 2       | Constraints                                                                             | Read Operation 1                                                  | Read Operation 2                                       |
| --- | -------------------------------- | ------------------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------ |
| 1   | movie_info_db.movie_info._id | movie_id_db.movie._id | PRIMARY KEY (movie_info_db.movie_info._id), PRIMARY KEY (movie_id_db.movie._id) | MovieInfoService.ReadMovieInfo → movie_info_db.movie_info.FindOne | MovieIdService.ReadMovieId → movie_id_db.movie.FindOne |

## Un-1: Uniqueness - Concurrent Writes

| #   | Constrained Field       | Constraint                       | Constrained Write Operation                                                             | Affected Write Operation                                             |
| --- | ----------------------- | -------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| 1   | movie_id_db.movie.Title | UNIQUE (movie_id_db.movie.Title) | APIService.RegisterMovie → MovieIdService.RegisterMovieId → movie_id_db.movie.InsertOne | MovieInfoService.WriteMovieInfo → movie_info_db.movie_info.InsertOne |
