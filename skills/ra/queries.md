# Resident Advisor GraphQL: Query fields
Based on the live introspection schema of https://ra.co/graphql (schema snapshot 2026-10-18).

Root `Query` fields with arguments and return types. Prefixes `Ticketing_`, `Embeddable_` and the payment/guestlist/presale/HelpScout fields need promoter or user authentication.

```graphql
  helpScoutConfigs(sort: String, limit: Int, start: Int, where: JSON, publicationState: PublicationState): [HelpScoutConfig]
  metadataOverrides(sort: String, limit: Int, start: Int, where: JSON, publicationState: PublicationState): [MetadataOverride]
  ticketNotificationSubscriptions(eventId: ID, limit: Int): TicketNotificationSubscriptionsResponse!  # Lists ticket notifications subscriptions
  ticketNotificationsSubscriptions(eventId: ID, limit: Int): [TicketNotificationsSubscription!]! @deprecated  # Lists ticket notifications subscriptions
  Ticketing_aggregateOrders(_count: Ticketing_OrderAggregateArgsCount, where: Ticketing_FindManyOrderWhere): Ticketing_AggregateOrder  # Aggregate orders
  Ticketing_aggregateTicketTiers(_count: Ticketing_TicketTierAggregateArgsCount, where: Ticketing_FindManyTicketTiersV2WhereInput): Ticketing_AggregateTicketTier  # Aggregate ticket tiers
  Ticketing_barcode(where: Ticketing_BarcodeIdWhereUniqueInput!): Ticketing_Barcode  # Find a single barcode
  Ticketing_barcodes(orderBy: [Ticketing_FindManyBarcodeArgsOrderBy!], skip: Int, take: Int = 10, where: Ticketing_FindManyBarcodeArgsWhere): [Ticketing_Barcode!]!  # Find all barcodes
  Ticketing_basket(where: Ticketing_BasketIdWhereInput!): Ticketing_Basket  # Find basket
  Ticketing_event(where: Ticketing_EventLegacyIdWhereInput!): Ticketing_Event  # Find a single event
  Ticketing_globalSetting(settingName: String!): Ticketing_GlobalSetting  # Get global setting by setting name
  Ticketing_globalSettings: [Ticketing_GlobalSetting!]!  # Get all global settings
  Ticketing_me: Ticketing_UserV2  # Obtain current user
  Ticketing_order(where: Ticketing_OrderIdOrNumberWhereInput!): Ticketing_Order  # Find order
  Ticketing_orders(orderBy: [Ticketing_OrderOrderByWithRelationInput!], skip: Int, take: Int = 10, where: Ticketing_FindManyOrderWhere): [Ticketing_Order!]!  # Lists orders
  Ticketing_pinEvent: Ticketing_PinEvent!  # Get pin event data
  Ticketing_pins(eventId: String): [Ticketing_Pin!]!  # Find event pins
  Ticketing_promoterFeeDisplayTypes(promoterId: String!): Ticketing_PromoterFeeDisplayTypes  # Promoter fee display types settings
  Ticketing_promoterSetting(promoterId: String!, settingName: Ticketing_PromoterSettingsNameType!): Ticketing_PromoterSetting  # Get promoter setting by promoter id and setting name
  Ticketing_promoterSettings(promoterId: String!): [Ticketing_PromoterSetting!]!  # Get all promoter settings by promoter id
  Ticketing_savedCards: [Ticketing_SavedCard!]!  # Get SavedCard
  Ticketing_scannerBarcodes(eventId: UUID!, since: DateTime, skip: Int, take: Int = 5000): [Ticketing_ScannerBarcode!]!  # Get barcode data for an event for use with the ticket scanner
  Ticketing_ticketTierV2(where: Ticketing_TicketTierV2WhereInput!): Ticketing_TicketTierV2  # Find a ticket tier
  Ticketing_ticketTiersV2(orderBy: [Ticketing_TicketTierOrderByWithRelationInput!], promoCodes: [String!]! = [], queryType: Ticketing_TicketTiersQueryType = ALL, skip: Int, take: Int = 10, where: Ticketing_FindManyTicketTiersV2WhereInput): [Ticketing_TicketTierV2!]!  # Lists ticket tiers by event
  Ticketing_validationSchemas: Ticketing_ValidationSchemas!  # Fetch validation schemas
  Embeddable_generateMultiEventToken(tokenRequest: Embeddable_MultiEventTokenRequest!): Embeddable_Token!
  Embeddable_generateToken(tokenRequest: Embeddable_TokenRequest!): Embeddable_Token!
  bump(eventId: ID!): BumpsObject
  bumpValidation(currencyCode: String!): BumpsValidationObject
  bumps(areaId: ID, dateRange: DateRangeInput, page: Int = 1, type: ZoneType = ALL): BumpDecisionObject
  eventListingsBumps(areaId: ID!, events: [BumpEventInput!]!): EventListingBumpDecision
  isSignedUpToPresale(eventId: ID!): Boolean!
  presale(eventId: ID!): Presale
  presaleStatus(eventId: ID!): PresaleStatus
  sourceArtist(id: ID!): SourceArtist!  # Gets a Source artist
  sourceSearch(input: SourceSearchInput!): SourceSearchResult!  # Searches for Source artists
  guestlist(input: GuestlistRequest!): GuestlistDto!
  Guestlist_validationSchemas: Guestlist_ValidationSchemas!  # Fetch validation schemas
  paymentUser(promoterId: ID): PaymentUser
  paymentUsers(promoterIds: [ID]): [PaymentUser]
  authorizationObject(authorizationObject: AuthorizationObjectInput!): AuthorizationObjectType!  # Get an AuthorizationObject such as a resource or subject
  checkAuthorized(permission: String!, resource: AuthorizationObjectInput!): Boolean!  # Check if user has permissions for this resource
  checkManyAuthorized(input: [CheckAuthorizedInput!]!): [Boolean!]!  # Checks if the user has permissions for many resources. Returns results in the same order as the input
  checkPinAuthorized(permission: String!, pin: String!, resource: AuthorizationObjectInput!): Boolean!  # Check if a PIN has permissions for this resource
  checkPinManyAuthorized(input: [CheckAuthorizedInput!]!, pin: String!): [Boolean!]!  # Checks if a PIN has permissions for many resources. Returns results in the same order as the input
  permissions(resource: AuthorizationObjectInput!): [String!]!  # Get all permissions a user has for this resource
  news(limit: Int, pageNumber: Int, dateFrom: DateTime, dateTo: DateTime, types: [NewsType!], excludeIds: [ID], areaId: ID, orderBy: OrderByType, headline: Boolean): [News]
  newsArticle(id: ID): News
  exchanges(limit: Int, dateFrom: DateTime, dateTo: DateTime): [Exchange]
  podcast(id: ID): Podcast
  podcasts(limit: Int, dateFrom: DateTime, dateTo: DateTime): [Podcast]
  features(limit: Int, type: FeatureType, orderBy: OrderByType, featuredOnly: Boolean, videoType: VideoType, featureSeriesId: ID, dateFrom: DateTime, dateTo: DateTime, excludeIds: [ID]): [Feature]
  reviews(limit: Int, type: ReviewType, recommended: Boolean, orderBy: OrderByType, genre: String, dateFrom: DateTime, dateTo: DateTime, contentType: ReviewContentType): [Review]
  localNews(areaId: ID, limit: Int, types: [NewsType!]): [News]
  exchange(id: ID): Exchange
  label(id: ID): Label
  venue(id: ID, ensureLive: Boolean): Venue
  event(id: ID, includeOffline: Boolean): Event
  ticketTier(id: ID): Ticket
  locales: [LocaleDto]
  venues(limit: Int, areaId: ID, orderBy: OrderByType!, closed: Boolean): [Venue]
  artist(id: ID, slug: String): Artist
  promoter(id: ID, ensureLive: Boolean): Promoter
  promoters(limit: Int, areaId: ID, orderBy: OrderByType): [Promoter]
  genres: [Genre]
  feature(id: ID): Feature
  ips(countryId: ID, limit: Int): [IPSItem]
  microsite(slug: String): Microsite
  review(id: ID): Review
  multipleFeatureSeries(type: FeatureType): [FeatureSeries]
  singleFeatureSeries(seriesRef: String, type: FeatureType): FeatureSeries
  search(searchTerm: String, limit: Int, indices: [IndexType!], includeNonLive: Boolean, excludeIds: [String]): [Search]
  eventsListing(dateFrom: DateTime, dateTo: DateTime, areaId: ID): [GroupedEvents] @deprecated
  events(limit: Int, areaId: ID, type: EventQueryType!, orderBy: PickOrderByType, dateFrom: DateTime, dateTo: DateTime, ids: [ID]): [Event]
  user: User
  contributor(username: String): User
  area(id: ID, areaUrlName: String, countryUrlCode: String): Area
  areas(searchTerm: String, ids: [ID], limit: Int, defaultOnError: Boolean): [Area]
  autolocateArea(defaultOnError: Boolean): [Area]
  country(id: ID, urlCode: String): [Country]
  countries: [Country]
  shareCount(path: String): ShareCount
  listing(indexType: IndexType, indices: [IndexType!], aggregations: [ListingAggregationType!], filters: [FilterInput], sortField: FilterSortFieldType, sortOrder: FilterSortOrderType, page: Int, pageSize: Int): Listing
  eventListings(filters: FilterInputDtoInput, filterOptions: FilterOptionsInputDtoInput, page: Int, pageSize: Int, sort: SortInputDtoInput): EventListings
  facetedSearch(types: [IndexType!], filters: FilterInputDtoInput, filterOptions: FilterOptionsInputDtoInput, page: Int, pageSize: Int, sort: SortInputDtoInput): FacetedSearch
  currency(id: ID, isoCode: String): Currency
  currencies: [Currency]
  warmup: Boolean!
  taggedLineup(lineup: String, excludeArtistIds: [String]): TaggedLineup
  genders: [GenderDto]
  marketingCommunications: [MarketingCommunicationDto]
  priceWholesale(currencyCode: String, priceRetail: Decimal!, eventId: ID): Decimal
  priceRetail(currencyCode: String, priceWholesale: Decimal!, eventId: ID): Decimal
  soundCloudPlaylists: [SoundCloudPlaylist]
  eventListingsWithBumps(areaId: ID, filters: FilterInputDtoInput, filterOptions: FilterOptionsInputDtoInput, page: Int, pageSize: Int, sort: SortInputDtoInput): EventListingsWithBumps
  validationSchemas: ValidationSchemas
  multiEventDashboard(dashboard: String, ids: [ID]): Embeddable_Token
```
