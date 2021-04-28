SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

IF OBJECT_ID('store.RaiseError', 'P') IS NOT NULL
    DROP PROCEDURE [store].[RaiseError]
GO

CREATE PROCEDURE [store].[RaiseError]
AS

THROW 50001, 'Error', 1;