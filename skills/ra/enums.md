# Resident Advisor GraphQL: Enums and unions
Based on the live introspection schema of https://ra.co/graphql (schema snapshot 2026-10-18).

```graphql
enum App { WEBSITE RAGUIDE APPWEBVIEW ADMIN WEBAPI GRAPHQLAPI }
enum ApplyPolicy { BEFORE_RESOLVER AFTER_RESOLVER VALIDATION }
enum ApprovalStatusType { APPROVED PENDING }
enum ArtistStatus { PENDING TOP1000 REGIONAL DENIED }
enum BumpStatus { COMPLETED LIVE OUT_OF_BUDGET }
enum EventArtistsOrderByType { DEFAULT FOLLOWING }
enum EventQueryType { PICKS TODAY FROMDATE LATEST PREVIOUS ARCHIVE POPULAR FIRST ONDATE MAILERPICKS BYIDS }
enum EventRevisionApprovedStatusType { PENDING ARCHIVED CURRENT DENIED }
enum EventRole { INVOICE TICKETFEES }
enum EventStatus { PENDING LIVE }
enum EventSubmissionSource { SUBMITEVENTPAGE BULKUPLOADTOOL }
enum EventTicketsQueryType { AVAILABLE MANAGED }
enum ExternalMusicProvider { SPOTIFY }
enum FeatureHeaderImageType { STANDARD LARGE MOBILE VIDEOMP4 VIDEOWEBM ALL }
enum FeatureType { STANDARD TECH FILM }
enum FilterSortFieldType { DATE EVENTDATE REVIEWDATE NAME EVENTPOPULARITY }
enum FilterSortOrderType { ASCENDING DESCENDING }
enum GlobalSearchType { ARTIST VENUE PROMOTER AREA COUNTRY LABEL UPCOMINGEVENT PASTEVENT NEWS REVIEW FEATURE PODCAST EXCHANGE }
enum IPSItemColor { WHITE BLACK }
enum ImageType { FLYERFRONT FLYERBACK }
enum IndexType { EVENT ARTIST CLUB PROMOTER LABEL AREA NEWS REVIEW FEATURE PODCAST EXCHANGE }
enum Language { ENGLISH JAPANESE }
enum ListingAggregationType { ARTIST COUNTRY YEAR DATERANGE PROMOTER CLUB GENRE REVIEWTYPE LANGUAGE RECOMMENDED AUTHOR INDEX IDS EVENTTYPE PICK AREA }
enum Locale { en ja es fr it de nl pt pt_br es_mx pl }
enum MarketingSourceType { REGISTERSTANDARD REGISTERCHECKOUT REGISTERCHECKOUTWIDGET CHECKOUT CHECKOUTWIDGET MARKETINGSETTINGSPAGE UNKNOWN ITERABLEEMAILUNSUBSCRIBE LEGACYNEWSLETTERUNSUBSCRIBEPAGE LEGACYSUBSCRIPTIONSETTINGSPAGE LEGACYACCOUNTSETTINGSPAGE PROMOTERCREATEDAUTOENROLL ONECLICKUNSUBSCRIBE }
union Morph = UsersPermissionsMe | UsersPermissionsMeRole | UsersPermissionsLoginPayload | UserPermissionsPasswordPayload | HelpScoutBeacon | HelpScoutBeaconConnection | HelpScoutBeaconAggregator | HelpScoutBeaconGroupBy | HelpScoutBeaconConnectionId | HelpScoutBeaconConnectionCreated_at | HelpScoutBeaconConnectionUpdated_at | HelpScoutBeaconConnectionName | HelpScoutBeaconConnectionBeaconId | HelpScoutBeaconConnectionPublished_at | createHelpScoutBeaconPayload | updateHelpScoutBeaconPayload | deleteHelpScoutBeaconPayload | HelpScoutConfig | HelpScoutConfigConnection | HelpScoutConfigAggregator | HelpScoutConfigGroupBy | HelpScoutConfigConnectionId | HelpScoutConfigConnectionCreated_at | HelpScoutConfigConnectionUpdated_at | HelpScoutConfigConnectionUrl | HelpScoutConfigConnectionScreen | HelpScoutConfigConnectionHelpScoutBeacon | HelpScoutConfigConnectionPublished_at | createHelpScoutConfigPayload | updateHelpScoutConfigPayload | deleteHelpScoutConfigPayload | HelpScoutCustomFields | HelpScoutCustomFieldsConnection | HelpScoutCustomFieldsAggregator | HelpScoutCustomFieldsAggregatorSum | HelpScoutCustomFieldsAggregatorAvg | HelpScoutCustomFieldsAggregatorMin | HelpScoutCustomFieldsAggregatorMax | HelpScoutCustomFieldsGroupBy | HelpScoutCustomFieldsConnectionId | HelpScoutCustomFieldsConnectionCreated_at | HelpScoutCustomFieldsConnectionUpdated_at | HelpScoutCustomFieldsConnectionFieldName | HelpScoutCustomFieldsConnectionFieldId | HelpScoutCustomFieldsConnectionPublished_at | createHelpScoutCustomFieldPayload | updateHelpScoutCustomFieldPayload | deleteHelpScoutCustomFieldPayload | MetadataOverride | MetadataOverrideConnection | MetadataOverrideAggregator | MetadataOverrideGroupBy | MetadataOverrideConnectionId | MetadataOverrideConnectionCreated_at | MetadataOverrideConnectionUpdated_at | MetadataOverrideConnectionTitle | MetadataOverrideConnectionDescription | MetadataOverrideConnectionUrl | MetadataOverrideConnectionPublished_at | createMetadataOverridePayload | updateMetadataOverridePayload | deleteMetadataOverridePayload | I18NLocale | UploadFile | UploadFileConnection | UploadFileAggregator | UploadFileAggregatorSum | UploadFileAggregatorAvg | UploadFileAggregatorMin | UploadFileAggregatorMax | UploadFileGroupBy | UploadFileConnectionId | UploadFileConnectionCreated_at | UploadFileConnectionUpdated_at | UploadFileConnectionName | UploadFileConnectionAlternativeText | UploadFileConnectionCaption | UploadFileConnectionWidth | UploadFileConnectionHeight | UploadFileConnectionFormats | UploadFileConnectionHash | UploadFileConnectionExt | UploadFileConnectionMime | UploadFileConnectionSize | UploadFileConnectionUrl | UploadFileConnectionPreviewUrl | UploadFileConnectionProvider | UploadFileConnectionProvider_metadata | deleteFilePayload | UsersPermissionsPermission | UsersPermissionsRole | UsersPermissionsRoleConnection | UsersPermissionsRoleAggregator | UsersPermissionsRoleGroupBy | UsersPermissionsRoleConnectionId | UsersPermissionsRoleConnectionName | UsersPermissionsRoleConnectionDescription | UsersPermissionsRoleConnectionType | createRolePayload | updateRolePayload | deleteRolePayload | UsersPermissionsUser | UsersPermissionsUserConnection | UsersPermissionsUserAggregator | UsersPermissionsUserGroupBy | UsersPermissionsUserConnectionId | UsersPermissionsUserConnectionCreated_at | UsersPermissionsUserConnectionUpdated_at | UsersPermissionsUserConnectionUsername | UsersPermissionsUserConnectionEmail | UsersPermissionsUserConnectionProvider | UsersPermissionsUserConnectionConfirmed | UsersPermissionsUserConnectionBlocked | UsersPermissionsUserConnectionRole | createUserPayload | updateUserPayload | deleteUserPayload
enum NewsType { RAONRA RAPRO LOCAL INTERNATIONAL GENERAL TECH MAGAZINE FESTIVAL PLAYLIST MIXOFTHEDAY }
enum NullsOrder { first last }
enum OrderByType { LATEST POPULAR ALPHABETICAL }
enum PaymentExclusionType { BLOCK MONTHLY }
enum PickOrderByType { LATEST THISWEEK THISWEEKEND }
enum PitchType { FEATURE NEWS REVIEW }
enum Platform { IOS ANDROID WINDOWSPHONE }
enum PresaleStatus { ACTIVE COMPLETED }
enum ProfileType { INDIVIDUAL BUSINESS }
enum PromoterFeatureType { TRACKING EVENTDUPLICATION SECRETVENUE DISABLESERVICEFEES }
enum PublicationState { LIVE PREVIEW }
enum QueryMode { default insensitive }
enum ReviewContentType { ALL SHORTFORM LONGFORM }
enum ReviewType { ALBUM EVENT MOVIE TECH SINGLE SHORTSINGLE REWIND ALL ALLMUSIC }
enum SavedArtistListArtistStatus { BOOKED CONTACTED DECLINED NO_REPLY }
enum SetTimesStatusType { NONE SET PUBLIC PASSED }
enum SocialMediaPlatformType { INSTAGRAM YOUTUBE TELEGRAM DISCORD FACEBOOK TWITTER SOUNDCLOUD }
enum SortOrder { asc desc }
enum SortOrderType { ASCENDING DESCENDING }
enum SourceSavedArtistListScalarFieldEnum { areaId countryId date dateCreated dateUpdated ianaTimeZone id latitude longitude name userId }
enum SourceSavedArtistScalarFieldEnum { artistId dateUpdated userId }
enum SourceSavedArtist_SavedArtistListScalarFieldEnum { agentFee artistId bookingFee dateCreated dateUpdated listId notes status travelFee userId }
enum SourceSearchSortOrder { ASC DESC }
enum SuggestedArtistsType { DEBUT LOCAL NEARBY TOURING }
enum TemplateType { NONE FACEBOOK_PIXEL GOOGLE_ECOMMERCE DFP_CONVERSION TIKTOK_PIXEL }
enum TicketFeeType { UNKNOWN BOOKINGFEE SERVICEFEE ELECTEDBOOKINGFEE }
enum TicketNotificationSubscriptionType { ONSALE RESALE }
enum TicketTierStatus { DRAFT PENDING LIVE DENIED }
enum TicketTierType { ALL TICKETS ADDONS }
enum TicketValidType { VALID NOTYETONSALE NOLONGERONSALE SOLDOUT QUANTITYGREATERTHANTICKETSAVAILABLE STATUSCHANGEDTONOSELL DEPENDANCY HIDETICKET NOTYETONSALECOMBO }
enum TicketingSystem { LEGACY ENTIRE }
enum Ticketing_BarcodeInvalidationReason { guestlistGuestDeleted importedBarcodeDeleted manuallyInvalidated paymentPlanCancelled refunded regenerated resale }
enum Ticketing_BarcodeType { guestlist imported paid }
enum Ticketing_BaseCalculationField { RETAIL_PRICE WHOLESALE_PRICE }
enum Ticketing_BasketFlowType { multiSelect multiSelectStepped standard }
enum Ticketing_EventTagType { Free ResaleActive SalesEnded SoldOut }
enum Ticketing_EventTicketStatus { approved cancelled deleted pending stopped }
enum Ticketing_FeeDisplayType { hidden visible }
enum Ticketing_FeeType { booking service }
enum Ticketing_FulfilmentStatus { completed failed processing }
enum Ticketing_GlobalSettingsNameType { MAX_TICKETS_PER_BASKET MAX_TICKET_TIER_PER_FREE_ORDER MAX_TICKET_TIER_PER_ORDER MIN_FEE_AMOUNT MIN_TICKET_TIER_PER_ORDER TITLE_CAPS_PERCENT }
enum Ticketing_NullsOrder { first last }
enum Ticketing_OrderPaymentMethod { apple_pay card pay_pal pay_pal_pay_later payment_plan }
enum Ticketing_OrderSourceType { androidGuide iosGuide unknown web }
enum Ticketing_OrderStatus { authorization_pending authorized cancelled captured completed failed processing }
enum Ticketing_PaymentPlanPeriodUnit { day month week }
enum Ticketing_PaymentPlanStatus { active cancelled completed failed payment_intent_authorized }
enum Ticketing_PaymentType { APPLE_PAY CARD PAY_PAL PAY_PAL_PAY_LATER }
enum Ticketing_PinStatus { expired valid }
enum Ticketing_PromoterSettingsNameType { MIN_TICKET_TIER_ALLOCATION TITLE_CAPS_PERCENT }
enum Ticketing_QueryMode { default insensitive }
enum Ticketing_RefundSource { DoorRejection PromoterRefunded RaRefunded Resale SelfServe }
enum Ticketing_RefundStatus { awaiting_reconciliation awaiting_refund failed partially_refunded refunded }
enum Ticketing_ResaleStatus { available sold }
enum Ticketing_RetailChannelCodes { AUSTRALIA BELGIUM BRAZIL CANADA EUROZONE MEXICO NETHERLAND UK USA }
enum Ticketing_ScanAction { reject reset scan }
enum Ticketing_ScanResult { already_rejected already_scanned doesNotExist incorrectGate invalid refunded rejected reset scanned }
enum Ticketing_ScanStatus { invalid rejected scanned unscanned valid }
enum Ticketing_SortOrder { asc desc }
enum Ticketing_TicketCostType { donation free price }
union Ticketing_TicketListingItem = Ticketing_TicketGroup | Ticketing_TicketStep | Ticketing_TicketTierV2
enum Ticketing_TicketModelType { multipass standard upsell }
enum Ticketing_TicketNameType { custom default }
enum Ticketing_TicketNotificationSubscriptionAvailability { None OnSale Resale }
union Ticketing_TicketPromoAction = Ticketing_DiscountFixedPromoActionOut | Ticketing_DiscountPercentagePromoActionOut | Ticketing_HiddenPromoActionOut
enum Ticketing_TicketPromoActionType { discountFixed discountPercentage hidden }
enum Ticketing_TicketPromoDistributionType { invite promo }
enum Ticketing_TicketTierApprovalSource { AUTO MANUAL }
enum Ticketing_TicketTierApprovalStatus { approved pending rejected }
enum Ticketing_TicketTierDisplayStatus { available pending soldOut }
enum Ticketing_TicketTierInactivityReason { cancelled deleted stopped }
enum Ticketing_TicketTierRevisionLogType { allocation approvalStatus currency feeAmount inactivityReason onSaleEnd onSaleStart previousTicketTier retailPrice title visible wholesalePrice }
enum Ticketing_TicketTierSaleStatusName { Cancelled CurrentlyOnResale CurrentlyOnSale Deleted Error Pending PendingDependencySale PendingOnSale PendingSoldOut Rejected SaleEnd SaleStopped SoldOut }
enum Ticketing_TicketTiersQueryType { ALL AVAILABLE NON_REJECTED }
enum Ticketing_TransactionLogType { barcodeInvalidated barcodeRegenerated barcodeRevalidated basketAssigned basketCreated basketHiddenTickets basketMaxFreeTickets basketMaxOrderQuantityPerEvent basketMaxOrderQuantityPerTier basketMinOrderQuantityPerEvent basketMinOrderQuantityPerTier basketMixedCurrencies basketMixedRetailChannels basketNoMoreTickets basketUpdated basketZeroPriceTicketsOnly chargebeeApplyPaymentScheduleSchemeFailed chargebeeApplyPaymentScheduleSchemeStarted chargebeeApplyPaymentScheduleSchemeSuccessful chargebeeAssignPaymentSourceFailed chargebeeAssignPaymentSourceStarted chargebeeAssignPaymentSourceSuccessful chargebeeCreateInvoiceFailed chargebeeCreateInvoiceStarted chargebeeCreateInvoiceSuccessful chargebeeStartPaymentPlanCheckoutFailed chargebeeStartPaymentPlanCheckoutStarted chargebeeStartPaymentPlanCheckoutSuccessful orderCompleted orderCreated orderItemRefundUnmarked orderProcessingFailed orderUpdated orderVerificationFailed orderVerificationSuccessful payPalCreateOrderFailed payPalCreateOrderStarted payPalCreateOrderSuccessful paymentAuthorized paymentCancelFailed paymentCancelled paymentCaptureFailed paymentCaptured paymentFailed paymentIntentFailed paymentPlanStatusUpdateFailed paymentPlanStatusUpdated paymentSessionStarted paymentStatusCheckFailed paymentSuccessful refundCreated refundDbSaveFailed refundFailed refundSuccessful refundUpdated resaleItemPurchased savedCardDeletingFailed savedCardsObtainingFailed threeDSAttempted threeDSFailed threeDSRequired unknown updatedOrderWithPaymentResponse }
enum TrackingType { PAGEVIEW CONVERSION }
enum TransferMethodType { BANK_ACCOUNT PAYPAL_ACCOUNT VENMO_ACCOUNT WIRE_ACCOUNT }
enum UserEventType { EVENTSWITHTICKETS }
enum UserRegistrationSource { UNSPECIFIED WEBSTANDARD WEBCHECKOUT WEBFACEBOOK RAGUIDESTANDARD RAGUIDECHECKOUT RAGUIDEFACEBOOK RAGUIDEGUESTCHECKOUT RAGUIDEEXGUESTCHECKOUT WIDGET RANEXTSTANDARD RANEXTFACEBOOK RAGUIDECHECKOUTFACEBOOK RAGUIDEAPPLE RAGUIDECHECKOUTAPPLE RANEXTCHECKOUT }
enum VideoType { ALL FILM STREAM CLIP LIVENOW }
enum VisibilityType { PUBLIC HIDDEN SCHEDULED }
enum ZoneType { ALL POPULAR }
```
