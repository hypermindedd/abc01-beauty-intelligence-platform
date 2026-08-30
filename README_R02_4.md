# ABC.01 — R02.4 Tenant / Auth / Salon Config Boundaries

R02.4 establishes explicit tenant, role, salon-configuration, secret and persistence boundaries without claiming production infrastructure that does not yet exist.

## Roles

- `SALON_OWNER`
- `SALON_ADMIN`
- `SPECIALIST`
- `CONFIG_EDITOR`
- `READ_ONLY`

The role model is permission-based and fail-closed. Specialist Validation permission is reserved for the specialist role; secret management is reserved for the salon owner.

## Tenant / salon scope

`TenantContext` binds a principal to one tenant and salon. Session and configuration scope guards reject cross-tenant and cross-salon access.

## Infrastructure ports

R02.4 defines interfaces for:

- authentication;
- canonical session persistence;
- salon configuration persistence;
- tenant-scoped secret retrieval.

Interface existence is not production capability.

## Capability truth

Default infrastructure status is explicitly `INTERFACE_ONLY` for AUTH, PERSISTENCE, SECRETS and SALON_CONFIG. The runtime may only treat an infrastructure capability as available when its status is explicitly `VERIFIED` by an actual adapter and evidence.

## Non-claims

- production auth: not implemented;
- production persistence: not implemented;
- production secret store: not implemented;
- production salon-config store: not implemented;
- runtime product validation: not claimed;
- pilot readiness: not claimed;
- production readiness: not claimed.
