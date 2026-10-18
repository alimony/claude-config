# Resident Advisor GraphQL: Input types
Based on the live introspection schema of https://ra.co/graphql (schema snapshot 2026-10-18).

```graphql
input AddGuestlistGuestInput {
  allocation: Int!
  email: String
  eventId: ID!
  name: String!
}

input AddressInput {
  addressLine1: String!
  addressLine2: String
  city: String!
  stateProvince: String
  country: String!
  postalCode: String!
}

input AuthorizationObjectInput {
  email: String
  id: ID
  type: String!
}

input BoolFilterInputDtoInput {
  eq: Boolean!
}

input BumpEventInput {
  date: DateTime!
  id: ID!
}

input BumpsInputObject {
  acknowledge: Boolean!
  billing: Boolean!
  budget: Float!
  cpc: Float!
  endDate: DateTime!
  eventId: ID!
  startDate: DateTime!
}

input BumpsUpdateObject {
  acknowledge: Boolean!
  billing: Boolean!
  budget: Float!
  cpc: Float!
  eventId: ID!
}

input CheckAuthorizedInput {
  permission: String!
  resource: AuthorizationObjectInput!
}

input ConversionTestEventInput {
  testEventCode: String
  trackingCode: String
  authToken: String
  type: TemplateType!
}

input ConvertGuestUserInput {
  username: ID!
  password: ID!
}

input DateRangeFilterInputDtoInput {
  gt: DateTime
  lt: DateTime
  gte: DateTime
  lte: DateTime
}

input DateRangeInput {
  endDate: DateTime
  startDate: DateTime!
}

input DateTimeFilter {
  equals: DateTime
  gt: DateTime
  gte: DateTime
  in: [DateTime!]
  lt: DateTime
  lte: DateTime
  not: NestedDateTimeFilter
  notIn: [DateTime!]
}

input DateTimeNullableFilter {
  equals: DateTime
  gt: DateTime
  gte: DateTime
  in: [DateTime!]
  lt: DateTime
  lte: DateTime
  not: NestedDateTimeNullableFilter
  notIn: [DateTime!]
}

input DeleteGuestlistGuestInput {
  eventId: ID!
  guestId: ID!
}

input DeletePresaleInput {
  eventId: ID!
}

input Embeddable_MultiEventTokenRequest {
  dashboard: String!
  eventIds: [ID!]!
}

input Embeddable_TokenRequest {
  dashboard: String!
  eventId: ID!
}

input EnumSavedArtistListArtistStatusNullableFilter {
  equals: SavedArtistListArtistStatus
  in: [SavedArtistListArtistStatus!]
  not: NestedEnumSavedArtistListArtistStatusNullableFilter
  notIn: [SavedArtistListArtistStatus!]
}

input EventArtist {
  artistId: ID
  eventId: ID
}

input EventInput {
  startTime: DateTime!
  endTime: DateTime!
  title: StrippedHtml!
  lineup: StrippedHtml!
  venueId: ID
  areaId: ID
  venueTba: Boolean
  cost: StrippedHtml
  content: StrippedHtml
  minimumAge: Byte
  promoterIds: [ID]
  genreIds: [ID]
  promotionalLinks: [WebsiteInput]
  embargoDate: DateTime
  hideFromListings: Boolean
  images: [ImageInput]
  tbaVenueName: StrippedHtml
  playerLinks: [PlayerLinkInput]
  secretVenueReveal: SecretVenueRevealInput
  submissionSource: EventSubmissionSource
  visibility: VisibilityType
}

input ExistsFilterInputDtoInput {
  field: String
  eq: Boolean!
}

input FacebookTestEventInput {
  testEventCode: String
  trackingCode: String
  authToken: String
}

input FileInfoInput {
  name: String
  alternativeText: String
  caption: String
}

input FileInput {
  name: String!
  alternativeText: String
  caption: String
  width: Int
  height: Int
  formats: JSON
  hash: String!
  ext: String
  mime: String!
  size: Float!
  url: String!
  previewUrl: String
  provider: String!
  provider_metadata: JSON
  related: [ID]
  created_by: ID
  updated_by: ID
}

input FilterInput {
  type: ListingAggregationType!
  value: String!
}

input FilterInputDtoInput {
  date: DateRangeFilterInputDtoInput
  eventDatePosted: DateRangeFilterInputDtoInput
  listingDate: DateRangeFilterInputDtoInput
  startTime: UtcDateRangeFilterInputDtoInput
  endTime: UtcDateRangeFilterInputDtoInput
  area: IntFilterInputDtoInput
  areas: IntFilterInputDtoInput
  eventStatus: IntFilterInputDtoInput
  listingPosition: IntFilterInputDtoInput
  eventType: IntFilterInputDtoInput
  eventIds: IntFilterInputDtoInput
  newsLocalityType: IntFilterInputDtoInput
  newsType: IntFilterInputDtoInput
  isTicketed: BoolFilterInputDtoInput
  isSoldOut: BoolFilterInputDtoInput
  isPick: BoolFilterInputDtoInput
  isExcludedFromMailers: BoolFilterInputDtoInput
  newsHeadline: BoolFilterInputDtoInput
  live: BoolFilterInputDtoInput
  id: StringFilterInputDtoInput
  genre: StringFilterInputDtoInput
  name: StringFilterInputDtoInput
  title: MatchFilterInputDtoInput
  location: LocationFilterInputDtoInput
  exists: ExistsFilterInputDtoInput
  any: FilterInputDtoInput
  all: FilterInputDtoInput
}

input FilterOptionsInputDtoInput {
  genre: Boolean = false
  eventType: Boolean = false
  location: LocationFilterOptionsInputDtoInput
}

input FloatNullableFilter {
  equals: Float
  gt: Float
  gte: Float
  in: [Float!]
  lt: Float
  lte: Float
  not: NestedFloatNullableFilter
  notIn: [Float!]
}

input GuestlistRequest {
  eventId: ID!
  page: Float!
  pageSize: Float!
}

input HelpScoutBeaconInput {
  name: String!
  beaconId: String!
  helpScoutConfigs: [ID]
  customFields: [ID]
  published_at: DateTime
  created_by: ID
  updated_by: ID
}

input HelpScoutConfigInput {
  url: String
  screen: String
  helpScoutBeacon: ID
  published_at: DateTime
  created_by: ID
  updated_by: ID
}

input HelpScoutCustomFieldInput {
  fieldName: String
  fieldId: Int
  published_at: DateTime
  created_by: ID
  updated_by: ID
}

input ImageCropInput {
  x: Int
  y: Int
  height: Int
  width: Int
  unit: StrippedHtml
}

input ImageInput {
  id: ID
  filename: StrippedHtml!
  alt: StrippedHtml
  crop: ImageCropInput
  type: ImageType
}

input InputID {
  id: ID!
}

input IntFilterInputDtoInput {
  eq: Int
  any: [Int!]
  neq: Int
  none: [Int!]
}

input LocaleInput {
  name: String
  code: String
  created_by: ID
  updated_by: ID
}

input LocationFilterInputDtoInput {
  latitude: Float!
  longitude: Float!
  distance: String
}

input LocationFilterOptionsInputDtoInput {
  latitude: Float!
  longitude: Float!
}

input MatchFilterInputDtoInput {
  value: String
}

input MetadataOverrideInput {
  title: String
  description: String
  url: String!
  published_at: DateTime
  created_by: ID
  updated_by: ID
}

input NestedDateTimeFilter {
  equals: DateTime
  gt: DateTime
  gte: DateTime
  in: [DateTime!]
  lt: DateTime
  lte: DateTime
  not: NestedDateTimeFilter
  notIn: [DateTime!]
}

input NestedDateTimeNullableFilter {
  equals: DateTime
  gt: DateTime
  gte: DateTime
  in: [DateTime!]
  lt: DateTime
  lte: DateTime
  not: NestedDateTimeNullableFilter
  notIn: [DateTime!]
}

input NestedEnumSavedArtistListArtistStatusNullableFilter {
  equals: SavedArtistListArtistStatus
  in: [SavedArtistListArtistStatus!]
  not: NestedEnumSavedArtistListArtistStatusNullableFilter
  notIn: [SavedArtistListArtistStatus!]
}

input NestedFloatNullableFilter {
  equals: Float
  gt: Float
  gte: Float
  in: [Float!]
  lt: Float
  lte: Float
  not: NestedFloatNullableFilter
  notIn: [Float!]
}

input NestedStringFilter {
  contains: String
  endsWith: String
  equals: String
  gt: String
  gte: String
  in: [String!]
  lt: String
  lte: String
  not: NestedStringFilter
  notIn: [String!]
  startsWith: String
}

input NestedStringNullableFilter {
  contains: String
  endsWith: String
  equals: String
  gt: String
  gte: String
  in: [String!]
  lt: String
  lte: String
  not: NestedStringNullableFilter
  notIn: [String!]
  startsWith: String
}

input PaymentInput {
  promoterId: ID!
  amount: Float!
  currency: String!
}

input PaymentUserInput {
  promoterId: ID!
  profileType: ProfileType!
  businessName: String
  address: AddressInput!
  dateOfBirth: Date
  firstName: String
  lastName: String
  email: String
}

input PitchInput {
  type: PitchType!
  title: String!
  body: String!
}

input PlayerLinkInput {
  id: ID
  sourceId: StrippedHtml!
}

input PresaleInput {
  eventId: ID!
  onSaleFrom: DateTime!
  promoCodeId: String!
  scheduledEmailDate: DateTime!
  ticketId: String!
}

input PresaleUsersInput {
  eventId: String!
  signedUpAt: DateTime!
}

input PromoterInput {
  id: ID
  name: String
  areaId: ID
  termsAgreement: Boolean
}

input RoleInput {
  name: String!
  description: String
  type: String
  permissions: [ID]
  users: [ID]
  created_by: ID
  updated_by: ID
}

input SecretVenueRevealInput {
  revealDate: DateTime
  message: SecureSanitizedHtml!
  emailOnSubmit: Boolean!
}

input SendGuestEmailInput {
  eventId: ID!
  guestIds: [ID!]!
}

input SortInputDtoInput {
  eventDate: SortValueInput
  attending: SortValueInput
  interestedCount: SortValueInput
  eventDatePosted: SortValueInput
  listingDate: SortValueInput
  eventStatus: SortValueInput
  name: SortValueInput
  score: SortValueInput
  titleKeyword: SortValueInput
  date: SortValueInput
  newsViews: SortValueInput
}

input SortOrderInput {
  nulls: NullsOrder
  sort: SortOrder!
}

input SortValueInput {
  priority: Int
  order: FilterSortOrderType!
}

input SourceRecommendationFiltersInput {
  user: SourceSearchTermFilterInput
}

input SourceRecommendationsArgs {
  filters: SourceRecommendationFiltersInput
  page: Int!
  pageSize: Int!
  sort: SourceRecommendationsSearchSortInput!
}

input SourceRecommendationsSearchSortInput {
  random: SourceSearchRandomSortValue
}

input SourceSavedArtistListGenreListRelationFilter {
  every: SourceSavedArtistListGenreWhereInput
  none: SourceSavedArtistListGenreWhereInput
  some: SourceSavedArtistListGenreWhereInput
}

input SourceSavedArtistListGenreOrderByRelationAggregateInput {
  _count: SortOrder
}

input SourceSavedArtistListGenreWhereInput {
  AND: [SourceSavedArtistListGenreWhereInput!]
  NOT: [SourceSavedArtistListGenreWhereInput!]
  OR: [SourceSavedArtistListGenreWhereInput!]
  list: SourceSavedArtistListRelationFilter
  listId: StringFilter
  slug: StringFilter
}

input SourceSavedArtistListOrderByWithRelationInput {
  areaId: SortOrder
  countryId: SortOrder
  date: SortOrderInput
  dateCreated: SortOrder
  dateUpdated: SortOrder
  genres: SourceSavedArtistListGenreOrderByRelationAggregateInput
  ianaTimeZone: SortOrder
  id: SortOrder
  latitude: SortOrderInput
  longitude: SortOrderInput
  name: SortOrder
  savedArtistList_savedArtists: SourceSavedArtist_SavedArtistListOrderByRelationAggregateInput
  userId: SortOrder
}

input SourceSavedArtistListRelationFilter {
  is: SourceSavedArtistListWhereInput
  isNot: SourceSavedArtistListWhereInput
}

input SourceSavedArtistListWhereInput {
  AND: [SourceSavedArtistListWhereInput!]
  NOT: [SourceSavedArtistListWhereInput!]
  OR: [SourceSavedArtistListWhereInput!]
  areaId: StringFilter
  countryId: StringFilter
  date: DateTimeNullableFilter
  dateCreated: DateTimeFilter
  dateUpdated: DateTimeFilter
  genres: SourceSavedArtistListGenreListRelationFilter
  ianaTimeZone: StringFilter
  id: StringFilter
  latitude: FloatNullableFilter
  longitude: FloatNullableFilter
  name: StringFilter
  savedArtistList_savedArtists: SourceSavedArtist_SavedArtistListListRelationFilter
  userId: StringFilter
}

input SourceSavedArtistListWhereUniqueInput {
  AND: [SourceSavedArtistListWhereInput!]
  NOT: [SourceSavedArtistListWhereInput!]
  OR: [SourceSavedArtistListWhereInput!]
  areaId: StringFilter
  countryId: StringFilter
  date: DateTimeNullableFilter
  dateCreated: DateTimeFilter
  dateUpdated: DateTimeFilter
  genres: SourceSavedArtistListGenreListRelationFilter
  ianaTimeZone: StringFilter
  id: String
  latitude: FloatNullableFilter
  longitude: FloatNullableFilter
  name: StringFilter
  savedArtistList_savedArtists: SourceSavedArtist_SavedArtistListListRelationFilter
  userId: StringFilter
}

input SourceSavedArtistOrderByWithRelationInput {
  artistId: SortOrder
  dateUpdated: SortOrder
  savedArtist_savedArtistLists: SourceSavedArtist_SavedArtistListOrderByRelationAggregateInput
  userId: SortOrder
}

input SourceSavedArtistRelationFilter {
  is: SourceSavedArtistWhereInput
  isNot: SourceSavedArtistWhereInput
}

input SourceSavedArtistUserIdArtistIdCompoundUniqueInput {
  artistId: String!
  userId: String!
}

input SourceSavedArtistWhereInput {
  AND: [SourceSavedArtistWhereInput!]
  NOT: [SourceSavedArtistWhereInput!]
  OR: [SourceSavedArtistWhereInput!]
  artistId: StringFilter
  dateUpdated: DateTimeFilter
  savedArtist_savedArtistLists: SourceSavedArtist_SavedArtistListListRelationFilter
  userId: StringFilter
}

input SourceSavedArtistWhereUniqueInput {
  AND: [SourceSavedArtistWhereInput!]
  NOT: [SourceSavedArtistWhereInput!]
  OR: [SourceSavedArtistWhereInput!]
  artistId: StringFilter
  dateUpdated: DateTimeFilter
  savedArtist_savedArtistLists: SourceSavedArtist_SavedArtistListListRelationFilter
  userId: StringFilter
  userId_artistId: SourceSavedArtistUserIdArtistIdCompoundUniqueInput
}

input SourceSavedArtist_SavedArtistListListRelationFilter {
  every: SourceSavedArtist_SavedArtistListWhereInput
  none: SourceSavedArtist_SavedArtistListWhereInput
  some: SourceSavedArtist_SavedArtistListWhereInput
}

input SourceSavedArtist_SavedArtistListOrderByRelationAggregateInput {
  _count: SortOrder
}

input SourceSavedArtist_SavedArtistListOrderByWithRelationInput {
  agentFee: SortOrderInput
  artistId: SortOrder
  bookingFee: SortOrderInput
  dateCreated: SortOrder
  dateUpdated: SortOrderInput
  listId: SortOrder
  notes: SortOrderInput
  savedArtist: SourceSavedArtistOrderByWithRelationInput
  savedArtistList: SourceSavedArtistListOrderByWithRelationInput
  status: SortOrderInput
  travelFee: SortOrderInput
  userId: SortOrder
}

input SourceSavedArtist_SavedArtistListWhereInput {
  AND: [SourceSavedArtist_SavedArtistListWhereInput!]
  NOT: [SourceSavedArtist_SavedArtistListWhereInput!]
  OR: [SourceSavedArtist_SavedArtistListWhereInput!]
  agentFee: FloatNullableFilter
  artistId: StringFilter
  bookingFee: FloatNullableFilter
  dateCreated: DateTimeFilter
  dateUpdated: DateTimeNullableFilter
  listId: StringFilter
  notes: StringNullableFilter
  savedArtist: SourceSavedArtistRelationFilter
  savedArtistList: SourceSavedArtistListRelationFilter
  status: EnumSavedArtistListArtistStatusNullableFilter
  travelFee: FloatNullableFilter
  userId: StringFilter
}

input SourceSearchDateRangeFilterInput {
  gte: DateTime
  lte: DateTime
}

input SourceSearchDistanceRangeInput {
  gte: String
  lte: String
}

input SourceSearchEventFilterInput {
  date: [SourceSearchDateRangeFilterInput!]
  location: SourceSearchLocationRangeFilterInput
}

input SourceSearchFiltersInput {
  area: SourceSearchTermFilterInput
  areasPlayedIn: SourceSearchTermFilterInput
  bookingsIncreasePercentage: [SourceSearchRangeFilterInput!]
  country: SourceSearchTermFilterInput
  event: SourceSearchEventFilterInput
  followerCount: [SourceSearchRangeFilterInput!]
  genre: SourceSearchTermFilterInput
  hasRAMixOfTheDay: Boolean
  hasRAPickEvent: Boolean
  hasRAPodcast: Boolean
  id: SourceSearchTermFilterInput
  isActive: Boolean
  name: SourceSearchTermFilterInput
  popularByAgeRange: SourceSearchTermFilterInput
  popularByArea: SourceSearchTermFilterInput
  totalEvents: [SourceSearchRangeFilterInput!]
  upcomingEvents: [SourceSearchRangeFilterInput!]
}

input SourceSearchInput {
  filters: SourceSearchFiltersInput
  page: Int!
  pageSize: Int!
  query: SourceSearchQueryInput
  sort: SourceSearchSortInput
}

input SourceSearchLocationRangeFilterInput {
  distance: SourceSearchDistanceRangeInput
  latitude: Float
  longitude: Float
}

input SourceSearchQueryInput {
  name: String
}

input SourceSearchRandomSortValue {
  seed: String
}

input SourceSearchRangeFilterInput {
  gt: Float
  gte: Float
  lt: Float
  lte: Float
}

input SourceSearchSortInput {
  bookingsIncreasePercentage: SourceSearchSortValue
  followerCount: SourceSearchSortValue
  name: SourceSearchSortValue
  random: SourceSearchRandomSortValue
  totalEvents: SourceSearchSortValue
  upcomingEvents: SourceSearchSortValue
}

input SourceSearchSortValue {
  order: SourceSearchSortOrder!
}

input SourceSearchTermFilterInput {
  all: [String!]
  any: [String!]
  eq: String
  neq: String
  none: [String!]
}

input StringFilter {
  contains: String
  endsWith: String
  equals: String
  gt: String
  gte: String
  in: [String!]
  lt: String
  lte: String
  mode: QueryMode
  not: NestedStringFilter
  notIn: [String!]
  startsWith: String
}

input StringFilterInputDtoInput {
  eq: String
  any: [String]
  neq: String
  none: [String]
}

input StringNullableFilter {
  contains: String
  endsWith: String
  equals: String
  gt: String
  gte: String
  in: [String!]
  lt: String
  lte: String
  mode: QueryMode
  not: NestedStringNullableFilter
  notIn: [String!]
  startsWith: String
}

input TicketTierInput {
  id: ID
  title: String
  eventId: ID!
  onSaleFrom: DateTime
  onSaleUntil: DateTime
  allocation: Int
  price: Decimal
  currencyCode: String
  includeBookingFeeForCustomer: Boolean
  visible: Boolean
  dependency: Int
}

input Ticketing_AddBasketItemInput {
  quantity: Int!
  ticketTierId: UUID!
}

input Ticketing_AddBasketItemsInput {
  basketItems: [Ticketing_AddBasketItemInput!]!
  promoCodes: [String!] = []
}

input Ticketing_AdminUpdateEventInput {
  customTermsAndConditions: String
}

input Ticketing_AdminUpdateTicketTierInput {
  allocation: Int
  approvalStatus: Ticketing_TicketTierApprovalStatus
  currencyCode: String
  description: String
  feeType: Ticketing_FeeType
  id: UUID!
  previousTicketTierId: UUID
  ticketCost: Ticketing_UpdateTicketCostInput!
  ticketSalesPeriod: Ticketing_CreateTicketSalesPeriodInput!
  title: String
  visible: Boolean
}

input Ticketing_BarcodeIdWhereInput {
  id: Ticketing_StringFilter
}

input Ticketing_BarcodeIdWhereUniqueInput {
  id: UUID
}

input Ticketing_BarcodeListRelationFilter {
  every: Ticketing_BarcodeWhereInput
  none: Ticketing_BarcodeWhereInput
  some: Ticketing_BarcodeWhereInput
}

input Ticketing_BarcodeNullableRelationFilter {
  is: Ticketing_BarcodeWhereInput
  isNot: Ticketing_BarcodeWhereInput
}

input Ticketing_BarcodeOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_BarcodeRelationFilter {
  is: Ticketing_BarcodeWhereInput
  isNot: Ticketing_BarcodeWhereInput
}

input Ticketing_BarcodeWhereInput {
  AND: [Ticketing_BarcodeWhereInput!]
  OR: [Ticketing_BarcodeWhereInput!]
  createdAt: Ticketing_DateTimeFilter
  guestId: Ticketing_StringNullableFilter
  id: Ticketing_StringFilter
  order: Ticketing_OrderRelationFilter
  orderItem: Ticketing_OrderItemRelationFilter
  ticketNumber: Ticketing_StringFilter
  ticketTier: Ticketing_TicketTierRelationFilter
}

input Ticketing_BarcodeWhereUniqueInput {
  AND: [Ticketing_BarcodeWhereInput!]
  NOT: [Ticketing_BarcodeWhereInput!]
  OR: [Ticketing_BarcodeWhereInput!]
  createdAt: Ticketing_DateTimeFilter
  eventBarcodeModels: Ticketing_EventBarcodeModelListRelationFilter
  guestId: Ticketing_StringNullableFilter
  id: UUID
  invalidatedBarcode: Ticketing_BarcodeNullableRelationFilter
  invalidationReason: Ticketing_EnumBarcodeInvalidationReasonNullableFilter
  order: Ticketing_OrderRelationFilter
  orderId: Ticketing_StringFilter
  orderItem: Ticketing_OrderItemRelationFilter
  orderItemId: Ticketing_StringFilter
  scans: Ticketing_ScanListRelationFilter
  ticketNumber: Ticketing_StringFilter
  ticketTier: Ticketing_TicketTierRelationFilter
  ticketTierId: Ticketing_StringFilter
  type: Ticketing_EnumBarcodeTypeFilter
  updatedAt: Ticketing_DateTimeFilter
  upgradedBarcode: Ticketing_BarcodeNullableRelationFilter
  upgradedBarcodeId: UUID
  userId: Ticketing_StringNullableFilter
  valid: Ticketing_BoolFilter
}

input Ticketing_BasketIdWhereInput {
  id: UUID
}

input Ticketing_BasketItemListRelationFilter {
  every: Ticketing_BasketItemWhereInput
  none: Ticketing_BasketItemWhereInput
  some: Ticketing_BasketItemWhereInput
}

input Ticketing_BasketItemOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_BasketItemRelationFilter {
  is: Ticketing_BasketItemWhereInput
  isNot: Ticketing_BasketItemWhereInput
}

input Ticketing_BasketItemWhereInput {
  AND: [Ticketing_BasketItemWhereInput!]
  NOT: [Ticketing_BasketItemWhereInput!]
  OR: [Ticketing_BasketItemWhereInput!]
  basket: Ticketing_BasketRelationFilter
  basketId: Ticketing_StringFilter
  fee: Ticketing_FloatFilter
  id: Ticketing_StringFilter
  orderItems: Ticketing_OrderItemListRelationFilter
  price: Ticketing_FloatFilter
  quantity: Ticketing_IntFilter
  ticketPromoId: Ticketing_StringNullableFilter
  ticketTier: Ticketing_TicketTierRelationFilter
  ticketTierId: Ticketing_StringFilter
  total: Ticketing_FloatFilter
}

input Ticketing_BasketListRelationFilter {
  every: Ticketing_BasketWhereInput
  none: Ticketing_BasketWhereInput
  some: Ticketing_BasketWhereInput
}

input Ticketing_BasketNullableRelationFilter {
  is: Ticketing_BasketWhereInput
  isNot: Ticketing_BasketWhereInput
}

input Ticketing_BasketOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_BasketOrderByWithRelationInput {
  basketItems: Ticketing_BasketItemOrderByRelationAggregateInput
  createdAt: Ticketing_SortOrder
  currency: Ticketing_CurrencyOrderByWithRelationInput
  currencyId: Ticketing_SortOrderInput
  expiresAt: Ticketing_SortOrder
  id: Ticketing_SortOrder
  order: Ticketing_OrderOrderByWithRelationInput
  total: Ticketing_SortOrder
  transactionLogs: Ticketing_TransactionLogOrderByRelationAggregateInput
  updatedAt: Ticketing_SortOrder
  userId: Ticketing_SortOrderInput
}

input Ticketing_BasketRelationFilter {
  is: Ticketing_BasketWhereInput
  isNot: Ticketing_BasketWhereInput
}

input Ticketing_BasketWhereInput {
  AND: [Ticketing_BasketWhereInput!]
  NOT: [Ticketing_BasketWhereInput!]
  OR: [Ticketing_BasketWhereInput!]
  basketItems: Ticketing_BasketItemListRelationFilter
  createdAt: Ticketing_DateTimeFilter
  currency: Ticketing_CurrencyNullableRelationFilter
  currencyId: Ticketing_StringNullableFilter
  expiresAt: Ticketing_DateTimeFilter
  id: Ticketing_StringFilter
  order: Ticketing_OrderNullableRelationFilter
  total: Ticketing_FloatFilter
  transactionLogs: Ticketing_TransactionLogListRelationFilter
  updatedAt: Ticketing_DateTimeFilter
  userId: Ticketing_StringNullableFilter
}

input Ticketing_BasketWhereUniqueInput {
  AND: [Ticketing_BasketWhereInput!]
  NOT: [Ticketing_BasketWhereInput!]
  OR: [Ticketing_BasketWhereInput!]
  basketItems: Ticketing_BasketItemListRelationFilter
  createdAt: Ticketing_DateTimeFilter
  currency: Ticketing_CurrencyNullableRelationFilter
  currencyId: Ticketing_StringNullableFilter
  expiresAt: Ticketing_DateTimeFilter
  id: UUID
  order: Ticketing_OrderNullableRelationFilter
  total: Ticketing_FloatFilter
  transactionLogs: Ticketing_TransactionLogListRelationFilter
  updatedAt: Ticketing_DateTimeFilter
  userId: String
}

input Ticketing_BoolFilter {
  equals: Boolean
  not: Ticketing_BoolFilter
}

input Ticketing_CalculateTicketCostInput {
  baseCalculationField: Ticketing_BaseCalculationField
  retailPrice: Decimal
  wholesalePrice: Decimal
}

input Ticketing_CountryFeeListRelationFilter {
  every: Ticketing_CountryFeeWhereInput
  none: Ticketing_CountryFeeWhereInput
  some: Ticketing_CountryFeeWhereInput
}

input Ticketing_CountryFeeOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_CountryFeeSettingsInput {
  countryId: UUID!
  percentage: Decimal!
  type: Ticketing_FeeType!
}

input Ticketing_CountryFeeWhereInput {
  AND: [Ticketing_CountryFeeWhereInput!]
  NOT: [Ticketing_CountryFeeWhereInput!]
  OR: [Ticketing_CountryFeeWhereInput!]
  country: Ticketing_CountryRelationFilter
  countryId: Ticketing_StringFilter
  id: Ticketing_StringFilter
  percentage: Ticketing_FloatFilter
  type: Ticketing_EnumFeeTypeFilter
}

input Ticketing_CountryListRelationFilter {
  every: Ticketing_CountryWhereInput
  none: Ticketing_CountryWhereInput
  some: Ticketing_CountryWhereInput
}

input Ticketing_CountryOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_CountryOrderByWithRelationInput {
  code: Ticketing_SortOrder
  code2: Ticketing_SortOrder
  createdAt: Ticketing_SortOrder
  defaultCurrency: Ticketing_CurrencyOrderByWithRelationInput
  defaultCurrencyId: Ticketing_SortOrder
  events: Ticketing_EventOrderByRelationAggregateInput
  feeDisplayTypes: Ticketing_SortOrder
  feeSettings: Ticketing_CountryFeeOrderByRelationAggregateInput
  feeSettingsDeprecated: Ticketing_FeeSettingOrderByRelationAggregateInput
  id: Ticketing_SortOrder
  title: Ticketing_SortOrder
  updatedAt: Ticketing_SortOrder
}

input Ticketing_CountryRelationFilter {
  is: Ticketing_CountryWhereInput
  isNot: Ticketing_CountryWhereInput
}

input Ticketing_CountryWhereInput {
  AND: [Ticketing_CountryWhereInput!]
  NOT: [Ticketing_CountryWhereInput!]
  OR: [Ticketing_CountryWhereInput!]
  code: Ticketing_StringFilter
  code2: Ticketing_StringFilter
  createdAt: Ticketing_DateTimeFilter
  defaultCurrency: Ticketing_CurrencyRelationFilter
  defaultCurrencyId: Ticketing_StringFilter
  events: Ticketing_EventListRelationFilter
  feeDisplayTypes: Ticketing_EnumFeeDisplayTypeNullableListFilter
  feeSettings: Ticketing_CountryFeeListRelationFilter
  feeSettingsDeprecated: Ticketing_FeeSettingListRelationFilter
  id: Ticketing_StringFilter
  title: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_CreateBasketInput {
  basketItems: [Ticketing_CreateBasketItemInput!]!
  promoCodes: [String!] = []
  userId: String
}

input Ticketing_CreateBasketItemInput {
  quantity: Int!
  ticketTierId: UUID!
}

input Ticketing_CreateCountryInput {
  code: String!
  code2: String!
  defaultCurrencyId: UUID!
  feeDisplayTypes: [Ticketing_FeeDisplayType!]
  title: String!
}

input Ticketing_CreateCurrencyInput {
  code: String!
  minFee: Decimal!
  title: String!
}

input Ticketing_CreateInvitesInput {
  actionData: Ticketing_PromoActionDataInput!
  count: Int!
  name: String!
  ticketTierIds: [UUID!]!
  type: Ticketing_TicketPromoActionType!
}

input Ticketing_CreateMerchantSessionInput {
  initiativeContext: String!
  validationURL: String!
}

input Ticketing_CreateOrderInput {
  basketId: UUID!
  paymentDetails: Ticketing_PaymentDetailsInput
  paymentPlan: Ticketing_PaymentPlanInput
  refundStatus: Ticketing_RefundStatus
  source: Ticketing_OrderSourceType = unknown
  subscribedToPromoterIds: [ID!]
  threeDSecureRequired: Boolean
  useRaNewsletter: Boolean = false
  userId: String
}

input Ticketing_CreateOrderNoteInput {
  content: String!
  orderId: UUID!
}

input Ticketing_CreatePayPalOrderInput {
  basketId: UUID!
  billingName: String
}

input Ticketing_CreatePromoInput {
  actionData: Ticketing_PromoActionDataInput
  code: String!
  legacyEventId: String
  ticketTierIds: [UUID!]
  type: Ticketing_TicketPromoActionType!
}

input Ticketing_CreateRefundInput {
  invalidate: Boolean! = true
  orderId: UUID!
  refundItems: [Ticketing_RefundItemInput!]!
  source: Ticketing_RefundSource!
}

input Ticketing_CreateSavedCardInput {
  cardToken: String!
  postcode: String!
}

input Ticketing_CreateTicketCostInput {
  baseCalculationField: Ticketing_BaseCalculationField
  retailPrice: Decimal
  type: Ticketing_TicketCostType!
  wholesalePrice: Decimal
}

input Ticketing_CreateTicketSalesPeriodInput {
  endDate: DateTime
  startDate: DateTime
  timeZone: TimeZone!
}

input Ticketing_CreateTicketTierInput {
  allocation: Int!
  description: String
  event: Ticketing_EventLegacyIdWhereInput!
  feeType: Ticketing_FeeType!
  ticketChainItem: Ticketing_TicketChainItemInput
  ticketCost: Ticketing_CreateTicketCostInput
  ticketSalesPeriod: Ticketing_CreateTicketSalesPeriodInput!
  title: String!
  visible: Boolean
}

input Ticketing_CurrencyNullableRelationFilter {
  is: Ticketing_CurrencyWhereInput
  isNot: Ticketing_CurrencyWhereInput
}

input Ticketing_CurrencyOrderByWithRelationInput {
  Basket: Ticketing_BasketOrderByRelationAggregateInput
  code: Ticketing_SortOrder
  createdAt: Ticketing_SortOrder
  defaultCountries: Ticketing_CountryOrderByRelationAggregateInput
  events: Ticketing_EventOrderByRelationAggregateInput
  id: Ticketing_SortOrder
  minFee: Ticketing_SortOrder
  orders: Ticketing_OrderOrderByRelationAggregateInput
  ticketTier: Ticketing_TicketTierOrderByRelationAggregateInput
  title: Ticketing_SortOrder
  updatedAt: Ticketing_SortOrder
}

input Ticketing_CurrencyRelationFilter {
  is: Ticketing_CurrencyWhereInput
  isNot: Ticketing_CurrencyWhereInput
}

input Ticketing_CurrencyWhereInput {
  AND: [Ticketing_CurrencyWhereInput!]
  Basket: Ticketing_BasketListRelationFilter
  NOT: [Ticketing_CurrencyWhereInput!]
  OR: [Ticketing_CurrencyWhereInput!]
  code: Ticketing_StringFilter
  createdAt: Ticketing_DateTimeFilter
  defaultCountries: Ticketing_CountryListRelationFilter
  events: Ticketing_EventListRelationFilter
  id: Ticketing_StringFilter
  minFee: Ticketing_IntFilter
  orders: Ticketing_OrderListRelationFilter
  ticketTier: Ticketing_TicketTierListRelationFilter
  title: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_DateTimeFilter {
  equals: DateTime
  gt: DateTime
  gte: DateTime
  in: [DateTime!]
  lt: DateTime
  lte: DateTime
  not: Ticketing_DateTimeFilter
  notIn: [DateTime!]
}

input Ticketing_DateTimeNullableFilter {
  equals: DateTime
  gt: DateTime
  gte: DateTime
  in: [DateTime!]
  lt: DateTime
  lte: DateTime
  not: Ticketing_DateTimeNullableFilter
  notIn: [DateTime!]
}

input Ticketing_EnumBarcodeInvalidationReasonNullableFilter {
  equals: Ticketing_BarcodeInvalidationReason
  in: [Ticketing_BarcodeInvalidationReason!]
  not: Ticketing_EnumBarcodeInvalidationReasonNullableFilter
  notIn: [Ticketing_BarcodeInvalidationReason!]
}

input Ticketing_EnumBarcodeTypeFilter {
  equals: Ticketing_BarcodeType
  in: [Ticketing_BarcodeType!]
  not: Ticketing_EnumBarcodeTypeFilter
  notIn: [Ticketing_BarcodeType!]
}

input Ticketing_EnumEventTicketStatusFilter {
  equals: Ticketing_EventTicketStatus
  in: [Ticketing_EventTicketStatus!]
  not: Ticketing_EnumEventTicketStatusFilter
  notIn: [Ticketing_EventTicketStatus!]
}

input Ticketing_EnumFeeDisplayTypeNullableFilter {
  equals: Ticketing_FeeDisplayType
  in: [Ticketing_FeeDisplayType!]
  not: Ticketing_EnumFeeDisplayTypeNullableFilter
  notIn: [Ticketing_FeeDisplayType!]
}

input Ticketing_EnumFeeDisplayTypeNullableListFilter {
  equals: [Ticketing_FeeDisplayType!]
  has: Ticketing_FeeDisplayType
  hasEvery: [Ticketing_FeeDisplayType!]
  hasSome: [Ticketing_FeeDisplayType!]
  isEmpty: Boolean
}

input Ticketing_EnumFeeTypeFilter {
  equals: Ticketing_FeeType
  in: [Ticketing_FeeType!]
  not: Ticketing_EnumFeeTypeFilter
  notIn: [Ticketing_FeeType!]
}

input Ticketing_EnumFeeTypeNullableFilter {
  equals: Ticketing_FeeType
  in: [Ticketing_FeeType!]
  not: Ticketing_EnumFeeTypeNullableFilter
  notIn: [Ticketing_FeeType!]
}

input Ticketing_EnumOrderStatusFilter {
  equals: Ticketing_OrderStatus
  in: [Ticketing_OrderStatus!]
  not: Ticketing_EnumOrderStatusFilter
  notIn: [Ticketing_OrderStatus!]
}

input Ticketing_EnumRefundSourceFilter {
  equals: Ticketing_RefundSource
  in: [Ticketing_RefundSource!]
  not: Ticketing_EnumRefundSourceFilter
  notIn: [Ticketing_RefundSource!]
}

input Ticketing_EnumRefundStatusNullableFilter {
  equals: Ticketing_RefundStatus
  in: [Ticketing_RefundStatus!]
  not: Ticketing_EnumRefundStatusNullableFilter
  notIn: [Ticketing_RefundStatus!]
}

input Ticketing_EnumScanActionFilter {
  equals: Ticketing_ScanAction
  in: [Ticketing_ScanAction!]
  not: Ticketing_EnumScanActionFilter
  notIn: [Ticketing_ScanAction!]
}

input Ticketing_EnumScanResultFilter {
  equals: Ticketing_ScanResult
  in: [Ticketing_ScanResult!]
  not: Ticketing_EnumScanResultFilter
  notIn: [Ticketing_ScanResult!]
}

input Ticketing_EnumScanStatusFilter {
  equals: Ticketing_ScanStatus
  in: [Ticketing_ScanStatus!]
  not: Ticketing_EnumScanStatusFilter
  notIn: [Ticketing_ScanStatus!]
}

input Ticketing_EnumTicketCostTypeFilter {
  equals: Ticketing_TicketCostType
  in: [Ticketing_TicketCostType!]
  not: Ticketing_EnumTicketCostTypeFilter
  notIn: [Ticketing_TicketCostType!]
}

input Ticketing_EnumTicketModelTypeFilter {
  equals: Ticketing_TicketModelType
  in: [Ticketing_TicketModelType!]
  not: Ticketing_EnumTicketModelTypeFilter
  notIn: [Ticketing_TicketModelType!]
}

input Ticketing_EnumTicketTierApprovalStatusFilter {
  equals: Ticketing_TicketTierApprovalStatus
  in: [Ticketing_TicketTierApprovalStatus!]
  not: Ticketing_EnumTicketTierApprovalStatusFilter
  notIn: [Ticketing_TicketTierApprovalStatus!]
}

input Ticketing_EnumTicketTierInactivityReasonNullableFilter {
  equals: Ticketing_TicketTierInactivityReason
  in: [Ticketing_TicketTierInactivityReason!]
  not: Ticketing_EnumTicketTierInactivityReasonNullableFilter
  notIn: [Ticketing_TicketTierInactivityReason!]
}

input Ticketing_EnumTransactionLogTypeFilter {
  equals: Ticketing_TransactionLogType
  in: [Ticketing_TransactionLogType!]
  not: Ticketing_EnumTransactionLogTypeFilter
  notIn: [Ticketing_TransactionLogType!]
}

input Ticketing_EventBarcodeModelListRelationFilter {
  every: Ticketing_EventBarcodeModelWhereInput
  none: Ticketing_EventBarcodeModelWhereInput
  some: Ticketing_EventBarcodeModelWhereInput
}

input Ticketing_EventBarcodeModelOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_EventBarcodeModelWhereInput {
  AND: [Ticketing_EventBarcodeModelWhereInput!]
  NOT: [Ticketing_EventBarcodeModelWhereInput!]
  OR: [Ticketing_EventBarcodeModelWhereInput!]
  barcode: Ticketing_BarcodeRelationFilter
  barcodeId: Ticketing_StringFilter
  createdAt: Ticketing_DateTimeFilter
  deviceId: Ticketing_StringNullableFilter
  event: Ticketing_EventRelationFilter
  eventId: Ticketing_StringFilter
  orderItem: Ticketing_OrderItemNullableRelationFilter
  orderItemId: Ticketing_StringFilter
  rejectedAt: Ticketing_DateTimeNullableFilter
  scanStatus: Ticketing_EnumScanStatusFilter
  scannedAt: Ticketing_DateTimeNullableFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_EventLegacyIdWhereInput {
  id: UUID
  legacyId: String
}

input Ticketing_EventListRelationFilter {
  every: Ticketing_EventWhereInput
  none: Ticketing_EventWhereInput
  some: Ticketing_EventWhereInput
}

input Ticketing_EventOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_EventOrderByWithRelationInput {
  country: Ticketing_CountryOrderByWithRelationInput
  countryId: Ticketing_SortOrder
  createdAt: Ticketing_SortOrder
  currency: Ticketing_CurrencyOrderByWithRelationInput
  currencyId: Ticketing_SortOrder
  endDate: Ticketing_SortOrder
  eventBarcodeModel: Ticketing_EventBarcodeModelOrderByRelationAggregateInput
  feeDisplayType: Ticketing_SortOrderInput
  feeSetting: Ticketing_FeeSettingOrderByWithRelationInput
  feeSettingId: Ticketing_SortOrder
  feeType: Ticketing_SortOrderInput
  id: Ticketing_SortOrder
  legacyId: Ticketing_SortOrder
  orderQuantity: Ticketing_EventOrderQuantityOrderByWithRelationInput
  owners: Ticketing_EventOwnerOrderByRelationAggregateInput
  pins: Ticketing_PinOrderByRelationAggregateInput
  promoterId: Ticketing_SortOrder
  scans: Ticketing_ScanOrderByRelationAggregateInput
  startDate: Ticketing_SortOrder
  ticketPromo: Ticketing_TicketPromoOrderByRelationAggregateInput
  ticketStatus: Ticketing_SortOrder
  ticketTiers: Ticketing_TicketTierOrderByRelationAggregateInput
  timeZone: Ticketing_SortOrder
  title: Ticketing_SortOrder
  updatedAt: Ticketing_SortOrder
  validTicketModels: Ticketing_TicketModelOrderByRelationAggregateInput
}

input Ticketing_EventOrderQuantityNullableRelationFilter {
  is: Ticketing_EventOrderQuantityWhereInput
  isNot: Ticketing_EventOrderQuantityWhereInput
}

input Ticketing_EventOrderQuantityOrderByWithRelationInput {
  createdAt: Ticketing_SortOrder
  event: Ticketing_EventOrderByWithRelationInput
  eventId: Ticketing_SortOrder
  id: Ticketing_SortOrder
  maxPerEvent: Ticketing_SortOrderInput
  maxPerTier: Ticketing_SortOrderInput
  minPerEvent: Ticketing_SortOrderInput
  minPerTier: Ticketing_SortOrderInput
  updatedAt: Ticketing_SortOrder
}

input Ticketing_EventOrderQuantityWhereInput {
  AND: [Ticketing_EventOrderQuantityWhereInput!]
  NOT: [Ticketing_EventOrderQuantityWhereInput!]
  OR: [Ticketing_EventOrderQuantityWhereInput!]
  createdAt: Ticketing_DateTimeFilter
  event: Ticketing_EventRelationFilter
  eventId: Ticketing_StringFilter
  id: Ticketing_StringFilter
  maxPerEvent: Ticketing_IntNullableFilter
  maxPerTier: Ticketing_IntNullableFilter
  minPerEvent: Ticketing_IntNullableFilter
  minPerTier: Ticketing_IntNullableFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_EventOwnerListRelationFilter {
  every: Ticketing_EventOwnerWhereInput
  none: Ticketing_EventOwnerWhereInput
  some: Ticketing_EventOwnerWhereInput
}

input Ticketing_EventOwnerOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_EventOwnerWhereInput {
  AND: [Ticketing_EventOwnerWhereInput!]
  NOT: [Ticketing_EventOwnerWhereInput!]
  OR: [Ticketing_EventOwnerWhereInput!]
  createdAt: Ticketing_DateTimeFilter
  email: Ticketing_StringNullableFilter
  event: Ticketing_EventRelationFilter
  eventId: Ticketing_StringFilter
  firstname: Ticketing_StringNullableFilter
  id: Ticketing_StringFilter
  lastname: Ticketing_StringNullableFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_EventRelationFilter {
  is: Ticketing_EventWhereInput
  isNot: Ticketing_EventWhereInput
}

input Ticketing_EventWhereInput {
  AND: [Ticketing_EventWhereInput!]
  NOT: [Ticketing_EventWhereInput!]
  OR: [Ticketing_EventWhereInput!]
  country: Ticketing_CountryRelationFilter
  countryId: Ticketing_StringFilter
  createdAt: Ticketing_DateTimeFilter
  currency: Ticketing_CurrencyRelationFilter
  currencyId: Ticketing_StringFilter
  endDate: Ticketing_DateTimeNullableFilter
  eventBarcodeModel: Ticketing_EventBarcodeModelListRelationFilter
  feeDisplayType: Ticketing_EnumFeeDisplayTypeNullableFilter
  feeSetting: Ticketing_FeeSettingRelationFilter
  feeSettingId: Ticketing_StringFilter
  feeType: Ticketing_EnumFeeTypeNullableFilter
  id: Ticketing_StringFilter
  legacyId: Ticketing_StringFilter
  orderQuantity: Ticketing_EventOrderQuantityNullableRelationFilter
  owners: Ticketing_EventOwnerListRelationFilter
  pins: Ticketing_PinListRelationFilter
  promoterId: Ticketing_StringFilter
  scans: Ticketing_ScanListRelationFilter
  startDate: Ticketing_DateTimeNullableFilter
  ticketPromo: Ticketing_TicketPromoListRelationFilter
  ticketStatus: Ticketing_EnumEventTicketStatusFilter
  ticketTiers: Ticketing_TicketTierListRelationFilter
  timeZone: Ticketing_StringFilter
  title: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
  validTicketModels: Ticketing_TicketModelListRelationFilter
}

input Ticketing_FailOrderInput {
  orderId: String!
  reason: String
  status: Ticketing_OrderStatus!
}

input Ticketing_FeeSettingListRelationFilter {
  every: Ticketing_FeeSettingWhereInput
  none: Ticketing_FeeSettingWhereInput
  some: Ticketing_FeeSettingWhereInput
}

input Ticketing_FeeSettingOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_FeeSettingOrderByWithRelationInput {
  countries: Ticketing_CountryOrderByRelationAggregateInput
  createdAt: Ticketing_SortOrder
  events: Ticketing_EventOrderByRelationAggregateInput
  id: Ticketing_SortOrder
  percentage: Ticketing_SortOrder
  type: Ticketing_SortOrder
  updatedAt: Ticketing_SortOrder
}

input Ticketing_FeeSettingRelationFilter {
  is: Ticketing_FeeSettingWhereInput
  isNot: Ticketing_FeeSettingWhereInput
}

input Ticketing_FeeSettingWhereInput {
  AND: [Ticketing_FeeSettingWhereInput!]
  NOT: [Ticketing_FeeSettingWhereInput!]
  OR: [Ticketing_FeeSettingWhereInput!]
  countries: Ticketing_CountryListRelationFilter
  createdAt: Ticketing_DateTimeFilter
  events: Ticketing_EventListRelationFilter
  id: Ticketing_StringFilter
  percentage: Ticketing_FloatFilter
  type: Ticketing_EnumFeeTypeFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_FindManyBarcodeArgsOrderBy {
  order: Ticketing_FindManyBarcodeArgsOrderByOrder
  orderItem: Ticketing_FindManyBarcodeArgsOrderByOrderItem
  ticketNumber: Ticketing_SortOrder
  ticketTier: Ticketing_FindManyBarcodeArgsOrderByTicketTier
}

input Ticketing_FindManyBarcodeArgsOrderByOrder {
  completedAt: Ticketing_SortOrder
  createdAt: Ticketing_SortOrder
  orderNumber: Ticketing_SortOrder
}

input Ticketing_FindManyBarcodeArgsOrderByOrderItem {
  refundStatus: Ticketing_SortOrderInput
}

input Ticketing_FindManyBarcodeArgsOrderByTicketTier {
  title: Ticketing_SortOrder
}

input Ticketing_FindManyBarcodeArgsWhere {
  AND: [Ticketing_FindManyBarcodeArgsWhere!]
  OR: [Ticketing_FindManyBarcodeArgsWhere!]
  createdAt: Ticketing_DateTimeFilter
  guestId: Ticketing_StringNullableFilter
  id: Ticketing_StringFilter
  order: Ticketing_FindManyBarcodeArgsWhereOrder
  orderItem: Ticketing_FindManyBarcodeArgsWhereOrderItem
  ticketNumber: Ticketing_StringFilter
  ticketTier: Ticketing_FindManyBarcodeArgsWhereTicketTier
}

input Ticketing_FindManyBarcodeArgsWhereOrder {
  is: Ticketing_FindManyBarcodeArgsWhereOrderIs
}

input Ticketing_FindManyBarcodeArgsWhereOrderIs {
  AND: [Ticketing_FindManyBarcodeArgsWhereOrderIs!]
  completedAt: Ticketing_DateTimeFilter
  createdAt: Ticketing_DateTimeFilter
}

input Ticketing_FindManyBarcodeArgsWhereOrderItem {
  is: Ticketing_FindManyBarcodeArgsWhereOrderItemIs
}

input Ticketing_FindManyBarcodeArgsWhereOrderItemIs {
  refundStatus: Ticketing_EnumRefundStatusNullableFilter
}

input Ticketing_FindManyBarcodeArgsWhereTicketTier {
  is: Ticketing_FindManyBarcodeArgsWhereTicketTierIs
}

input Ticketing_FindManyBarcodeArgsWhereTicketTierIs {
  title: Ticketing_StringFilter
}

input Ticketing_FindManyOrderArgsWhereOrderItems {
  some: Ticketing_FindManyOrderArgsWhereOrderItemsSome
}

input Ticketing_FindManyOrderArgsWhereOrderItemsSome {
  ticketTier: Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTier
}

input Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTier {
  is: Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIs
}

input Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIs {
  event: Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIsEvent
}

input Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIsEvent {
  is: Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIsEventIs
}

input Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIsEventIs {
  country: Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIsEventIsCountry
}

input Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIsEventIsCountry {
  is: Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIsEventIsCountryIs
}

input Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIsEventIsCountryIs {
  OR: [Ticketing_FindManyOrderArgsWhereOrderItemsSomeTicketTierIsEventIsCountryIs!]
  title: Ticketing_StringFilter
}

input Ticketing_FindManyOrderWhere {
  AND: [Ticketing_FindManyOrderWhere!]
  amount: Ticketing_FloatFilter
  billingName: Ticketing_StringFilter
  createdAt: Ticketing_DateTimeFilter
  fulfilmentStatus: Ticketing_FulfilmentStatus
  legacyEventId: Ticketing_StringFilter
  orderItems: Ticketing_FindManyOrderArgsWhereOrderItems
  orderNumber: Ticketing_StringFilter
  orderPaymentMethod: Ticketing_OrderPaymentMethod
}

input Ticketing_FindManyTicketTiersV2EventInput {
  legacyId: Ticketing_StringFilter
  title: Ticketing_StringFilter
}

input Ticketing_FindManyTicketTiersV2EventRelationInput {
  is: Ticketing_FindManyTicketTiersV2EventInput
  isNot: Ticketing_FindManyTicketTiersV2EventInput
}

input Ticketing_FindManyTicketTiersV2SalesPeriodInput {
  endDate: Ticketing_DateTimeNullableFilter
  startDate: Ticketing_DateTimeNullableFilter
}

input Ticketing_FindManyTicketTiersV2SalesPeriodRelationInput {
  is: Ticketing_FindManyTicketTiersV2SalesPeriodInput
  isNot: Ticketing_FindManyTicketTiersV2SalesPeriodInput
}

input Ticketing_FindManyTicketTiersV2WhereInput {
  OR: [Ticketing_FindManyTicketTiersV2WhereInput!]
  approvalStatus: Ticketing_EnumTicketTierApprovalStatusFilter
  event: Ticketing_FindManyTicketTiersV2EventRelationInput
  id: Ticketing_StringFilter
  ticketSalesPeriod: Ticketing_FindManyTicketTiersV2SalesPeriodRelationInput
  visible: Ticketing_BoolFilter
}

input Ticketing_FloatFilter {
  equals: Float
  gt: Float
  gte: Float
  in: [Float!]
  lt: Float
  lte: Float
  not: Ticketing_FloatFilter
  notIn: [Float!]
}

input Ticketing_HiddenTicketPromoListRelationFilter {
  every: Ticketing_HiddenTicketPromoWhereInput
  none: Ticketing_HiddenTicketPromoWhereInput
  some: Ticketing_HiddenTicketPromoWhereInput
}

input Ticketing_HiddenTicketPromoOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_HiddenTicketPromoWhereInput {
  AND: [Ticketing_HiddenTicketPromoWhereInput!]
  NOT: [Ticketing_HiddenTicketPromoWhereInput!]
  OR: [Ticketing_HiddenTicketPromoWhereInput!]
  code: Ticketing_StringFilter
  createdAt: Ticketing_DateTimeFilter
  id: Ticketing_StringFilter
  isActive: Ticketing_BoolFilter
  ticketTier: Ticketing_TicketTierRelationFilter
  ticketTierId: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
  url: Ticketing_StringFilter
}

input Ticketing_ImportExternalBarcodesInput {
  csvContent: String!
  legacyEventId: String!
  outlet: String!
}

input Ticketing_IntFilter {
  equals: Int
  gt: Int
  gte: Int
  in: [Int!]
  lt: Int
  lte: Int
  not: Ticketing_IntFilter
  notIn: [Int!]
}

input Ticketing_IntNullableFilter {
  equals: Int
  gt: Int
  gte: Int
  in: [Int!]
  lt: Int
  lte: Int
  not: Ticketing_IntNullableFilter
  notIn: [Int!]
}

input Ticketing_InvalidatePaidBarcodesInput {
  barcodeIds: [UUID!]!
}

input Ticketing_JsonFilter {
  array_contains: JSON
  array_ends_with: JSON
  array_starts_with: JSON
  equals: JSON
  gt: JSON
  gte: JSON
  lt: JSON
  lte: JSON
  not: JSON
  path: [String!]
  string_contains: String
  string_ends_with: String
  string_starts_with: String
}

input Ticketing_OrderAggregateArgsCount {
  _all: Boolean
}

input Ticketing_OrderIdOrNumberWhereInput {
  id: UUID
  orderNumber: String
}

input Ticketing_OrderItemListRelationFilter {
  every: Ticketing_OrderItemWhereInput
  none: Ticketing_OrderItemWhereInput
  some: Ticketing_OrderItemWhereInput
}

input Ticketing_OrderItemNullableRelationFilter {
  is: Ticketing_OrderItemWhereInput
  isNot: Ticketing_OrderItemWhereInput
}

input Ticketing_OrderItemOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_OrderItemRelationFilter {
  is: Ticketing_OrderItemWhereInput
  isNot: Ticketing_OrderItemWhereInput
}

input Ticketing_OrderItemWhereInput {
  AND: [Ticketing_OrderItemWhereInput!]
  NOT: [Ticketing_OrderItemWhereInput!]
  OR: [Ticketing_OrderItemWhereInput!]
  allBarcodes: Ticketing_BarcodeListRelationFilter
  basketItem: Ticketing_BasketItemRelationFilter
  basketItemId: Ticketing_StringFilter
  feeAmount: Ticketing_FloatFilter
  id: Ticketing_StringFilter
  order: Ticketing_OrderRelationFilter
  orderId: Ticketing_StringFilter
  refundItems: Ticketing_RefundItemListRelationFilter
  refundStatus: Ticketing_EnumRefundStatusNullableFilter
  retailAmount: Ticketing_FloatFilter
  ticketPromoId: Ticketing_StringNullableFilter
  ticketTier: Ticketing_TicketTierRelationFilter
  ticketTierId: Ticketing_StringFilter
}

input Ticketing_OrderItemWhereUniqueInput {
  AND: [Ticketing_OrderItemWhereInput!]
  NOT: [Ticketing_OrderItemWhereInput!]
  OR: [Ticketing_OrderItemWhereInput!]
  allBarcodes: Ticketing_BarcodeListRelationFilter
  basketItem: Ticketing_BasketItemRelationFilter
  basketItemId: Ticketing_StringFilter
  feeAmount: Ticketing_FloatFilter
  id: UUID
  order: Ticketing_OrderRelationFilter
  orderId: Ticketing_StringFilter
  refundItems: Ticketing_RefundItemListRelationFilter
  refundStatus: Ticketing_EnumRefundStatusNullableFilter
  retailAmount: Ticketing_FloatFilter
  ticketPromoId: Ticketing_StringNullableFilter
  ticketTier: Ticketing_TicketTierRelationFilter
  ticketTierId: Ticketing_StringFilter
}

input Ticketing_OrderListRelationFilter {
  every: Ticketing_OrderWhereInput
  none: Ticketing_OrderWhereInput
  some: Ticketing_OrderWhereInput
}

input Ticketing_OrderNoteListRelationFilter {
  every: Ticketing_OrderNoteWhereInput
  none: Ticketing_OrderNoteWhereInput
  some: Ticketing_OrderNoteWhereInput
}

input Ticketing_OrderNoteOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_OrderNoteWhereInput {
  AND: [Ticketing_OrderNoteWhereInput!]
  NOT: [Ticketing_OrderNoteWhereInput!]
  OR: [Ticketing_OrderNoteWhereInput!]
  content: Ticketing_StringFilter
  createdAt: Ticketing_DateTimeFilter
  id: Ticketing_StringFilter
  order: Ticketing_OrderRelationFilter
  orderId: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_OrderNullableRelationFilter {
  is: Ticketing_OrderWhereInput
  isNot: Ticketing_OrderWhereInput
}

input Ticketing_OrderOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_OrderOrderByWithRelationInput {
  amount: Ticketing_SortOrder
  barcodes: Ticketing_BarcodeOrderByRelationAggregateInput
  basket: Ticketing_BasketOrderByWithRelationInput
  basketId: Ticketing_SortOrder
  billingName: Ticketing_SortOrderInput
  completedAt: Ticketing_SortOrderInput
  createdAt: Ticketing_SortOrder
  currency: Ticketing_CurrencyOrderByWithRelationInput
  currencyId: Ticketing_SortOrder
  id: Ticketing_SortOrder
  orderItems: Ticketing_OrderItemOrderByRelationAggregateInput
  orderNotes: Ticketing_OrderNoteOrderByRelationAggregateInput
  orderNumber: Ticketing_SortOrder
  owners: Ticketing_OrderOwnerOrderByRelationAggregateInput
  paymentProvider: Ticketing_SortOrderInput
  refunds: Ticketing_RefundOrderByRelationAggregateInput
  status: Ticketing_SortOrder
  transactionId: Ticketing_SortOrderInput
  transactionLogs: Ticketing_TransactionLogOrderByRelationAggregateInput
  updatedAt: Ticketing_SortOrder
  userId: Ticketing_SortOrder
  userMarketingPreferencesLog: Ticketing_UserMarketingPreferencesLogOrderByWithRelationInput
  userMarketingPreferencesLogId: Ticketing_SortOrder
}

input Ticketing_OrderOwnerListRelationFilter {
  every: Ticketing_OrderOwnerWhereInput
  none: Ticketing_OrderOwnerWhereInput
  some: Ticketing_OrderOwnerWhereInput
}

input Ticketing_OrderOwnerOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_OrderOwnerWhereInput {
  AND: [Ticketing_OrderOwnerWhereInput!]
  NOT: [Ticketing_OrderOwnerWhereInput!]
  OR: [Ticketing_OrderOwnerWhereInput!]
  createdAt: Ticketing_DateTimeFilter
  email: Ticketing_StringNullableFilter
  firstname: Ticketing_StringNullableFilter
  id: Ticketing_StringFilter
  lastname: Ticketing_StringNullableFilter
  order: Ticketing_OrderNullableRelationFilter
  orderId: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_OrderRelationFilter {
  is: Ticketing_OrderWhereInput
  isNot: Ticketing_OrderWhereInput
}

input Ticketing_OrderWhereInput {
  AND: [Ticketing_OrderWhereInput!]
  NOT: [Ticketing_OrderWhereInput!]
  OR: [Ticketing_OrderWhereInput!]
  amount: Ticketing_FloatFilter
  barcodes: Ticketing_BarcodeListRelationFilter
  basket: Ticketing_BasketRelationFilter
  basketId: Ticketing_StringFilter
  billingName: Ticketing_StringFilter
  completedAt: Ticketing_DateTimeNullableFilter
  createdAt: Ticketing_DateTimeFilter
  currency: Ticketing_CurrencyRelationFilter
  currencyId: Ticketing_StringFilter
  id: Ticketing_StringFilter
  orderItems: Ticketing_OrderItemListRelationFilter
  orderNotes: Ticketing_OrderNoteListRelationFilter
  orderNumber: Ticketing_StringFilter
  owners: Ticketing_OrderOwnerListRelationFilter
  paymentProvider: Ticketing_StringNullableFilter
  refunds: Ticketing_RefundListRelationFilter
  status: Ticketing_EnumOrderStatusFilter
  transactionId: Ticketing_StringNullableFilter
  transactionLogs: Ticketing_TransactionLogListRelationFilter
  updatedAt: Ticketing_DateTimeFilter
  userId: Ticketing_StringFilter
  userMarketingPreferencesLog: Ticketing_UserMarketingPreferencesLogRelationFilter
  userMarketingPreferencesLogId: Ticketing_StringFilter
}

input Ticketing_PaymentDetailsInput {
  billingName: String
  payPalOrderId: String
  postcode: String
  token: String
  type: Ticketing_PaymentType = CARD
}

input Ticketing_PaymentPlanInput {
  chargebeePaymentIntentId: String!
  chargebeePaymentSchemeId: String!
}

input Ticketing_PinListRelationFilter {
  every: Ticketing_PinWhereInput
  none: Ticketing_PinWhereInput
  some: Ticketing_PinWhereInput
}

input Ticketing_PinOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_PinWhereInput {
  AND: [Ticketing_PinWhereInput!]
  NOT: [Ticketing_PinWhereInput!]
  OR: [Ticketing_PinWhereInput!]
  code: Ticketing_StringFilter
  createdAt: Ticketing_DateTimeFilter
  event: Ticketing_EventRelationFilter
  eventId: Ticketing_StringFilter
  id: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_PromoActionDataInput {
  allocation: Int
  discountAmount: Decimal
  discountPercentage: Decimal
}

input Ticketing_PromoterFeeSettingsInput {
  percentage: Float!
  promoterId: String!
  type: Ticketing_FeeType!
}

input Ticketing_RefundItemInput {
  amountPercentage: Float
  feeAmountPercentage: Float
  orderItemId: UUID!
  wholesaleAmountPercentage: Float
}

input Ticketing_RefundItemListRelationFilter {
  every: Ticketing_RefundItemWhereInput
  none: Ticketing_RefundItemWhereInput
  some: Ticketing_RefundItemWhereInput
}

input Ticketing_RefundItemWhereInput {
  AND: [Ticketing_RefundItemWhereInput!]
  NOT: [Ticketing_RefundItemWhereInput!]
  OR: [Ticketing_RefundItemWhereInput!]
  amount: Ticketing_FloatFilter
  createdAt: Ticketing_DateTimeFilter
  feeAmount: Ticketing_FloatFilter
  id: Ticketing_StringFilter
  orderItem: Ticketing_OrderItemRelationFilter
  orderItemId: Ticketing_StringFilter
  refund: Ticketing_RefundRelationFilter
  refundId: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_RefundListRelationFilter {
  every: Ticketing_RefundWhereInput
  none: Ticketing_RefundWhereInput
  some: Ticketing_RefundWhereInput
}

input Ticketing_RefundOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_RefundRelationFilter {
  is: Ticketing_RefundWhereInput
  isNot: Ticketing_RefundWhereInput
}

input Ticketing_RefundWhereInput {
  AND: [Ticketing_RefundWhereInput!]
  NOT: [Ticketing_RefundWhereInput!]
  OR: [Ticketing_RefundWhereInput!]
  amount: Ticketing_FloatFilter
  createdAt: Ticketing_DateTimeFilter
  feeAmount: Ticketing_FloatFilter
  id: Ticketing_StringFilter
  order: Ticketing_OrderRelationFilter
  orderId: Ticketing_StringFilter
  refundItems: Ticketing_RefundItemListRelationFilter
  source: Ticketing_EnumRefundSourceFilter
  updatedAt: Ticketing_DateTimeFilter
  userId: Ticketing_StringFilter
}

input Ticketing_RemoveBasketItemInput {
  ticketTierId: UUID!
}

input Ticketing_ScanListRelationFilter {
  every: Ticketing_ScanWhereInput
  none: Ticketing_ScanWhereInput
  some: Ticketing_ScanWhereInput
}

input Ticketing_ScanOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_ScanWhereInput {
  AND: [Ticketing_ScanWhereInput!]
  NOT: [Ticketing_ScanWhereInput!]
  OR: [Ticketing_ScanWhereInput!]
  action: Ticketing_EnumScanActionFilter
  barcode: Ticketing_BarcodeNullableRelationFilter
  barcodeId: Ticketing_StringNullableFilter
  createdAt: Ticketing_DateTimeFilter
  deviceId: Ticketing_StringNullableFilter
  event: Ticketing_EventRelationFilter
  eventId: Ticketing_StringFilter
  id: Ticketing_StringFilter
  result: Ticketing_EnumScanResultFilter
  scannedById: Ticketing_StringNullableFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_ScannerRecordBarcodeInput {
  action: Ticketing_ScanAction!
  actionTimestamp: DateTime!
  deviceId: String
  ticketNumber: String!
}

input Ticketing_ScannerRecordBarcodesInput {
  eventId: UUID!
  scans: [Ticketing_ScannerRecordBarcodeInput!]!
}

input Ticketing_SetPromoterSettingInput {
  name: Ticketing_PromoterSettingsNameType!
  promoterId: String!
  value: String!
}

input Ticketing_SortOrderInput {
  nulls: Ticketing_NullsOrder
  sort: Ticketing_SortOrder!
}

input Ticketing_StartPaymentPlanCheckoutInput {
  basketId: UUID!
}

input Ticketing_StringFilter {
  contains: String
  endsWith: String
  equals: String
  gt: String
  gte: String
  in: [String!]
  lt: String
  lte: String
  mode: Ticketing_QueryMode
  not: Ticketing_StringFilter
  notIn: [String!]
  startsWith: String
}

input Ticketing_StringNullableFilter {
  contains: String
  endsWith: String
  equals: String
  gt: String
  gte: String
  in: [String!]
  lt: String
  lte: String
  mode: Ticketing_QueryMode
  not: Ticketing_StringNullableFilter
  notIn: [String!]
  startsWith: String
}

input Ticketing_StringNullableListFilter {
  equals: [String!]
  has: String
  hasEvery: [String!]
  hasSome: [String!]
  isEmpty: Boolean
}

input Ticketing_TicketChainItemInput {
  previousId: ID
}

input Ticketing_TicketCostNullableRelationFilter {
  is: Ticketing_TicketCostWhereInput
  isNot: Ticketing_TicketCostWhereInput
}

input Ticketing_TicketCostOrderByWithRelationInput {
  createdAt: Ticketing_SortOrder
  id: Ticketing_SortOrder
  retailPrice: Ticketing_SortOrder
  ticketTier: Ticketing_TicketTierOrderByWithRelationInput
  ticketTierId: Ticketing_SortOrder
  type: Ticketing_SortOrder
  updatedAt: Ticketing_SortOrder
  wholesalePrice: Ticketing_SortOrder
}

input Ticketing_TicketCostWhereInput {
  AND: [Ticketing_TicketCostWhereInput!]
  NOT: [Ticketing_TicketCostWhereInput!]
  OR: [Ticketing_TicketCostWhereInput!]
  createdAt: Ticketing_DateTimeFilter
  id: Ticketing_StringFilter
  retailPrice: Ticketing_FloatFilter
  ticketTier: Ticketing_TicketTierRelationFilter
  ticketTierId: Ticketing_StringFilter
  type: Ticketing_EnumTicketCostTypeFilter
  updatedAt: Ticketing_DateTimeFilter
  wholesalePrice: Ticketing_FloatFilter
}

input Ticketing_TicketModelListRelationFilter {
  every: Ticketing_TicketModelWhereInput
  none: Ticketing_TicketModelWhereInput
  some: Ticketing_TicketModelWhereInput
}

input Ticketing_TicketModelOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_TicketModelOrderByWithRelationInput {
  baseTicketId: Ticketing_SortOrderInput
  baseTicketTier: Ticketing_TicketTierOrderByWithRelationInput
  createdAt: Ticketing_SortOrder
  id: Ticketing_SortOrder
  ticketTiers: Ticketing_TicketTierOrderByRelationAggregateInput
  type: Ticketing_SortOrder
  updatedAt: Ticketing_SortOrder
  validEvents: Ticketing_EventOrderByRelationAggregateInput
}

input Ticketing_TicketModelRelationFilter {
  is: Ticketing_TicketModelWhereInput
  isNot: Ticketing_TicketModelWhereInput
}

input Ticketing_TicketModelWhereInput {
  AND: [Ticketing_TicketModelWhereInput!]
  NOT: [Ticketing_TicketModelWhereInput!]
  OR: [Ticketing_TicketModelWhereInput!]
  baseTicketId: Ticketing_StringNullableFilter
  baseTicketTier: Ticketing_TicketTierNullableRelationFilter
  createdAt: Ticketing_DateTimeFilter
  id: Ticketing_StringFilter
  ticketTiers: Ticketing_TicketTierListRelationFilter
  type: Ticketing_EnumTicketModelTypeFilter
  updatedAt: Ticketing_DateTimeFilter
  validEvents: Ticketing_EventListRelationFilter
}

input Ticketing_TicketOrderQuantityNullableRelationFilter {
  is: Ticketing_TicketOrderQuantityWhereInput
  isNot: Ticketing_TicketOrderQuantityWhereInput
}

input Ticketing_TicketOrderQuantityOrderByWithRelationInput {
  createdAt: Ticketing_SortOrder
  id: Ticketing_SortOrder
  maxPerTier: Ticketing_SortOrder
  minPerTier: Ticketing_SortOrder
  ticketTier: Ticketing_TicketTierOrderByWithRelationInput
  ticketTierId: Ticketing_SortOrder
  updatedAt: Ticketing_SortOrder
}

input Ticketing_TicketOrderQuantityWhereInput {
  AND: [Ticketing_TicketOrderQuantityWhereInput!]
  NOT: [Ticketing_TicketOrderQuantityWhereInput!]
  OR: [Ticketing_TicketOrderQuantityWhereInput!]
  createdAt: Ticketing_DateTimeFilter
  id: Ticketing_StringFilter
  maxPerTier: Ticketing_IntFilter
  minPerTier: Ticketing_IntFilter
  ticketTier: Ticketing_TicketTierRelationFilter
  ticketTierId: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_TicketPromoListRelationFilter {
  every: Ticketing_TicketPromoWhereInput
  none: Ticketing_TicketPromoWhereInput
  some: Ticketing_TicketPromoWhereInput
}

input Ticketing_TicketPromoOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_TicketPromoWhereInput {
  AND: [Ticketing_TicketPromoWhereInput!]
  NOT: [Ticketing_TicketPromoWhereInput!]
  OR: [Ticketing_TicketPromoWhereInput!]
  code: Ticketing_StringFilter
  createdAt: Ticketing_DateTimeFilter
  discountAmount: Ticketing_FloatFilter
  discountPercentage: Ticketing_FloatFilter
  event: Ticketing_EventRelationFilter
  eventId: Ticketing_StringFilter
  id: Ticketing_StringFilter
  isActive: Ticketing_BoolFilter
  promoType: Ticketing_StringFilter
  ticketTierIds: Ticketing_StringNullableListFilter
  updatedAt: Ticketing_DateTimeFilter
  url: Ticketing_StringFilter
}

input Ticketing_TicketSalesPeriodNullableRelationFilter {
  is: Ticketing_TicketSalesPeriodWhereInput
  isNot: Ticketing_TicketSalesPeriodWhereInput
}

input Ticketing_TicketSalesPeriodOrderByWithRelationInput {
  createdAt: Ticketing_SortOrder
  endDate: Ticketing_SortOrderInput
  id: Ticketing_SortOrder
  startDate: Ticketing_SortOrderInput
  ticketTier: Ticketing_TicketTierOrderByWithRelationInput
  ticketTierId: Ticketing_SortOrder
  timeZone: Ticketing_SortOrder
  type: Ticketing_SortOrder
  updatedAt: Ticketing_SortOrder
}

input Ticketing_TicketSalesPeriodWhereInput {
  AND: [Ticketing_TicketSalesPeriodWhereInput!]
  NOT: [Ticketing_TicketSalesPeriodWhereInput!]
  OR: [Ticketing_TicketSalesPeriodWhereInput!]
  createdAt: Ticketing_DateTimeFilter
  endDate: Ticketing_DateTimeNullableFilter
  id: Ticketing_StringFilter
  startDate: Ticketing_DateTimeNullableFilter
  ticketTier: Ticketing_TicketTierRelationFilter
  ticketTierId: Ticketing_StringFilter
  timeZone: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_TicketScansWhereInput {
  barcodeTypes: [Ticketing_BarcodeType!]
  createdAt: Ticketing_DateTimeFilter
  deviceId: String
  scannedAt: Ticketing_TicketScansWhereScannedAtInput
}

input Ticketing_TicketScansWhereScannedAtInput {
  end: DateTime
  start: DateTime
}

input Ticketing_TicketTierAggregateArgsCount {
  _all: Boolean
}

input Ticketing_TicketTierFeeNullableRelationFilter {
  is: Ticketing_TicketTierFeeWhereInput
  isNot: Ticketing_TicketTierFeeWhereInput
}

input Ticketing_TicketTierFeeOrderByWithRelationInput {
  createdAt: Ticketing_SortOrder
  id: Ticketing_SortOrder
  isCustomMinFee: Ticketing_SortOrder
  isCustomPercentage: Ticketing_SortOrder
  minFee: Ticketing_SortOrder
  percentage: Ticketing_SortOrder
  ticketTier: Ticketing_TicketTierOrderByWithRelationInput
  type: Ticketing_SortOrder
  updatedAt: Ticketing_SortOrder
}

input Ticketing_TicketTierFeeWhereInput {
  AND: [Ticketing_TicketTierFeeWhereInput!]
  NOT: [Ticketing_TicketTierFeeWhereInput!]
  OR: [Ticketing_TicketTierFeeWhereInput!]
  createdAt: Ticketing_DateTimeFilter
  id: Ticketing_StringFilter
  isCustomMinFee: Ticketing_BoolFilter
  isCustomPercentage: Ticketing_BoolFilter
  minFee: Ticketing_FloatFilter
  percentage: Ticketing_FloatFilter
  ticketTier: Ticketing_TicketTierNullableRelationFilter
  type: Ticketing_EnumFeeTypeFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_TicketTierListRelationFilter {
  every: Ticketing_TicketTierWhereInput
  none: Ticketing_TicketTierWhereInput
  some: Ticketing_TicketTierWhereInput
}

input Ticketing_TicketTierNullableRelationFilter {
  is: Ticketing_TicketTierWhereInput
  isNot: Ticketing_TicketTierWhereInput
}

input Ticketing_TicketTierOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_TicketTierOrderByWithRelationInput {
  allocation: Ticketing_SortOrder
  approvalStatus: Ticketing_SortOrder
  approvalStatusUpdatedAt: Ticketing_SortOrderInput
  barcodes: Ticketing_BarcodeOrderByRelationAggregateInput
  basketItems: Ticketing_BasketItemOrderByRelationAggregateInput
  createdAt: Ticketing_SortOrder
  currency: Ticketing_CurrencyOrderByWithRelationInput
  currencyId: Ticketing_SortOrderInput
  dependentTicketModels: Ticketing_TicketModelOrderByRelationAggregateInput
  description: Ticketing_SortOrderInput
  event: Ticketing_EventOrderByWithRelationInput
  eventId: Ticketing_SortOrder
  feeSettings: Ticketing_TicketTierFeeOrderByWithRelationInput
  feeSettingsId: Ticketing_SortOrderInput
  hiddenTicketPromo: Ticketing_HiddenTicketPromoOrderByRelationAggregateInput
  id: Ticketing_SortOrder
  inactivityReason: Ticketing_SortOrderInput
  orderItems: Ticketing_OrderItemOrderByRelationAggregateInput
  orderQuantity: Ticketing_TicketOrderQuantityOrderByWithRelationInput
  owners: Ticketing_TicketTierOwnerOrderByRelationAggregateInput
  ticketCost: Ticketing_TicketCostOrderByWithRelationInput
  ticketModel: Ticketing_TicketModelOrderByWithRelationInput
  ticketModelId: Ticketing_SortOrder
  ticketSalesPeriod: Ticketing_TicketSalesPeriodOrderByWithRelationInput
  title: Ticketing_SortOrder
  updatedAt: Ticketing_SortOrder
  visible: Ticketing_SortOrder
}

input Ticketing_TicketTierOwnerListRelationFilter {
  every: Ticketing_TicketTierOwnerWhereInput
  none: Ticketing_TicketTierOwnerWhereInput
  some: Ticketing_TicketTierOwnerWhereInput
}

input Ticketing_TicketTierOwnerOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_TicketTierOwnerWhereInput {
  AND: [Ticketing_TicketTierOwnerWhereInput!]
  NOT: [Ticketing_TicketTierOwnerWhereInput!]
  OR: [Ticketing_TicketTierOwnerWhereInput!]
  TicketTier: Ticketing_TicketTierNullableRelationFilter
  createdAt: Ticketing_DateTimeFilter
  email: Ticketing_StringNullableFilter
  firstname: Ticketing_StringNullableFilter
  id: Ticketing_StringFilter
  lastname: Ticketing_StringNullableFilter
  ticketTierId: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
}

input Ticketing_TicketTierRelationFilter {
  is: Ticketing_TicketTierWhereInput
}

input Ticketing_TicketTierRevisionLogsAggregateArgsCount {
  _all: Boolean
}

input Ticketing_TicketTierV2WhereInput {
  id: UUID!
}

input Ticketing_TicketTierWhereInput {
  AND: [Ticketing_TicketTierWhereInput!]
  NOT: [Ticketing_TicketTierWhereInput!]
  OR: [Ticketing_TicketTierWhereInput!]
  allocation: Ticketing_IntFilter
  approvalStatus: Ticketing_EnumTicketTierApprovalStatusFilter
  barcodes: Ticketing_BarcodeListRelationFilter
  basketItems: Ticketing_BasketItemListRelationFilter
  createdAt: Ticketing_DateTimeFilter
  currency: Ticketing_CurrencyNullableRelationFilter
  currencyId: Ticketing_StringNullableFilter
  dependentTicketModels: Ticketing_TicketModelListRelationFilter
  description: Ticketing_StringNullableFilter
  event: Ticketing_EventRelationFilter
  eventId: Ticketing_StringFilter
  feeSettings: Ticketing_TicketTierFeeNullableRelationFilter
  feeSettingsId: Ticketing_StringNullableFilter
  hiddenTicketPromo: Ticketing_HiddenTicketPromoListRelationFilter
  id: Ticketing_StringFilter
  inactivityReason: Ticketing_EnumTicketTierInactivityReasonNullableFilter
  orderItems: Ticketing_OrderItemListRelationFilter
  orderQuantity: Ticketing_TicketOrderQuantityNullableRelationFilter
  owners: Ticketing_TicketTierOwnerListRelationFilter
  ticketCost: Ticketing_TicketCostNullableRelationFilter
  ticketModel: Ticketing_TicketModelRelationFilter
  ticketModelId: Ticketing_StringFilter
  ticketSalesPeriod: Ticketing_TicketSalesPeriodNullableRelationFilter
  title: Ticketing_StringFilter
  updatedAt: Ticketing_DateTimeFilter
  visible: Ticketing_BoolFilter
}

input Ticketing_TransactionLogListRelationFilter {
  every: Ticketing_TransactionLogWhereInput
  none: Ticketing_TransactionLogWhereInput
  some: Ticketing_TransactionLogWhereInput
}

input Ticketing_TransactionLogOrderByRelationAggregateInput {
  _count: Ticketing_SortOrder
}

input Ticketing_TransactionLogWhereInput {
  AND: [Ticketing_TransactionLogWhereInput!]
  NOT: [Ticketing_TransactionLogWhereInput!]
  OR: [Ticketing_TransactionLogWhereInput!]
  basket: Ticketing_BasketNullableRelationFilter
  basketId: Ticketing_StringNullableFilter
  createdAt: Ticketing_DateTimeFilter
  details: Ticketing_JsonFilter
  id: Ticketing_StringFilter
  order: Ticketing_OrderNullableRelationFilter
  orderId: Ticketing_StringNullableFilter
  ticketTierId: Ticketing_StringNullableFilter
  type: Ticketing_EnumTransactionLogTypeFilter
  updatedAt: Ticketing_DateTimeFilter
  userId: Ticketing_StringNullableFilter
}

input Ticketing_UpdateBasketInput {
  basketItems: [Ticketing_UpdateBasketItemInput!]
  promoCodes: [String!] = []
  userId: String
}

input Ticketing_UpdateBasketItemInput {
  quantity: Int!
  ticketTierId: UUID!
}

input Ticketing_UpdateOrderNoteInput {
  content: String!
  id: UUID!
}

input Ticketing_UpdatePaymentPlanStatusInput {
  orderId: String!
  paymentPlanStatus: Ticketing_PaymentPlanStatus!
}

input Ticketing_UpdatePromoInput {
  actionData: Ticketing_PromoActionDataInput
  ticketTierIds: [UUID!]
}

input Ticketing_UpdatePromoterFeeDisplayTypes {
  feeDisplayTypes: [Ticketing_FeeDisplayType!]!
  promoterId: String!
}

input Ticketing_UpdateTicketCostInput {
  baseCalculationField: Ticketing_BaseCalculationField
  retailPrice: Decimal
  type: Ticketing_TicketCostType
  wholesalePrice: Decimal
}

input Ticketing_UpdateTicketTierInput {
  allocation: Int
  description: String
  feeType: Ticketing_FeeType
  id: UUID!
  ticketCost: Ticketing_UpdateTicketCostInput!
  ticketSalesPeriod: Ticketing_CreateTicketSalesPeriodInput!
  title: String
  visible: Boolean
}

input Ticketing_UpsertEventResaleItemsInput {
  eventId: ID!
  orderItemIds: [ID!]
}

input Ticketing_UserMarketingPreferencesLogOrderByWithRelationInput {
  id: Ticketing_SortOrder
  order: Ticketing_OrderOrderByWithRelationInput
  useRaNewsletter: Ticketing_SortOrder
}

input Ticketing_UserMarketingPreferencesLogRelationFilter {
  is: Ticketing_UserMarketingPreferencesLogWhereInput
  isNot: Ticketing_UserMarketingPreferencesLogWhereInput
}

input Ticketing_UserMarketingPreferencesLogWhereInput {
  AND: [Ticketing_UserMarketingPreferencesLogWhereInput!]
  NOT: [Ticketing_UserMarketingPreferencesLogWhereInput!]
  OR: [Ticketing_UserMarketingPreferencesLogWhereInput!]
  id: Ticketing_StringFilter
  order: Ticketing_OrderNullableRelationFilter
  useRaNewsletter: Ticketing_BoolFilter
}

input Ticketing_VerifyOrderInput {
  nonce: String!
  orderId: UUID!
}

input TrackingEntryInput {
  type: TemplateType!
  code: String
  authToken: String
}

input UpdateUserMarketingCommunicationsInput {
  marketingCommunicationIds: [ID]!
  source: MarketingSourceType!
}

input UserAppSettingsInput {
  deviceId: UUID!
  devicePushToken: String
  appVersion: String!
  platformId: Platform!
  platformOS: String!
  device: String!
  app: App!
}

input UserInput {
  username: String!
  email: String!
  provider: String
  password: String
  resetPasswordToken: String
  confirmationToken: String
  confirmed: Boolean
  blocked: Boolean
  role: ID
  created_by: ID
  updated_by: ID
}

input UserPushSubscriptionInput {
  deviceId: UUID!
  pushNotificationTypeIds: [Int!]
  subscribed: Boolean!
  app: App!
}

input UserRegisterAppInput {
  firstName: String
  lastName: String
  username: String!
  email: String!
  areaId: ID!
  password: String
  cartId: ID
  userRegistrationSource: UserRegistrationSource!
  userAppSettings: UserAppSettingsInput!
}

input UserRegisterInput {
  username: String!
  firstName: String
  surname: String
  email: String!
  emailConfirmation: String!
  password: String
  oAuthIdToken: String
  areaId: ID!
  dateOfBirth: Date
  genderId: ID
  locale: Locale!
  subscribeToNewsletter: Boolean!
  userRegistrationSource: UserRegistrationSource!
}

input UsersPermissionsLoginInput {
  identifier: String!
  password: String!
  provider: String = "local"
}

input UsersPermissionsRegisterInput {
  username: String!
  email: String!
  password: String!
}

input UtcDateRangeFilterInputDtoInput {
  gt: UtcDateTime
  lt: UtcDateTime
  gte: UtcDateTime
  lte: UtcDateTime
}

input WebsiteInput {
  title: StrippedHtml!
  url: StrippedHtml!
}

input createHelpScoutBeaconInput {
  data: HelpScoutBeaconInput
}

input createHelpScoutConfigInput {
  data: HelpScoutConfigInput
}

input createHelpScoutCustomFieldInput {
  data: HelpScoutCustomFieldInput
}

input createMetadataOverrideInput {
  data: MetadataOverrideInput
}

input createRoleInput {
  data: RoleInput
}

input createUserInput {
  data: UserInput
}

input deleteFileInput {
  where: InputID
}

input deleteHelpScoutBeaconInput {
  where: InputID
}

input deleteHelpScoutConfigInput {
  where: InputID
}

input deleteHelpScoutCustomFieldInput {
  where: InputID
}

input deleteMetadataOverrideInput {
  where: InputID
}

input deleteRoleInput {
  where: InputID
}

input deleteUserInput {
  where: InputID
}

input editFileInput {
  name: String
  alternativeText: String
  caption: String
  width: Int
  height: Int
  formats: JSON
  hash: String
  ext: String
  mime: String
  size: Float
  url: String
  previewUrl: String
  provider: String
  provider_metadata: JSON
  related: [ID]
  created_by: ID
  updated_by: ID
}

input editHelpScoutBeaconInput {
  name: String
  beaconId: String
  helpScoutConfigs: [ID]
  customFields: [ID]
  published_at: DateTime
  created_by: ID
  updated_by: ID
}

input editHelpScoutConfigInput {
  url: String
  screen: String
  helpScoutBeacon: ID
  published_at: DateTime
  created_by: ID
  updated_by: ID
}

input editHelpScoutCustomFieldInput {
  fieldName: String
  fieldId: Int
  published_at: DateTime
  created_by: ID
  updated_by: ID
}

input editLocaleInput {
  name: String
  code: String
  created_by: ID
  updated_by: ID
}

input editMetadataOverrideInput {
  title: String
  description: String
  url: String
  published_at: DateTime
  created_by: ID
  updated_by: ID
}

input editRoleInput {
  name: String
  description: String
  type: String
  permissions: [ID]
  users: [ID]
  created_by: ID
  updated_by: ID
}

input editUserInput {
  username: String
  email: String
  provider: String
  password: String
  resetPasswordToken: String
  confirmationToken: String
  confirmed: Boolean
  blocked: Boolean
  role: ID
  created_by: ID
  updated_by: ID
}

input updateHelpScoutBeaconInput {
  where: InputID
  data: editHelpScoutBeaconInput
}

input updateHelpScoutConfigInput {
  where: InputID
  data: editHelpScoutConfigInput
}

input updateHelpScoutCustomFieldInput {
  where: InputID
  data: editHelpScoutCustomFieldInput
}

input updateMetadataOverrideInput {
  where: InputID
  data: editMetadataOverrideInput
}

input updateRoleInput {
  where: InputID
  data: editRoleInput
}

input updateUserInput {
  where: InputID
  data: editUserInput
}
```
