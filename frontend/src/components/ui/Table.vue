<template>
  <div class="overflow-x-auto rounded-xl border border-border-default">
    <table class="w-full border-collapse text-sm">
      <!-- Table Header -->
      <thead class="bg-bg-tertiary border-b border-border-default">
        <tr>
          <slot name="header" />
        </tr>
      </thead>

      <!-- Table Body -->
      <tbody>
        <slot />
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
// Table component - uses slots for flexibility
// Usage:
// <Table>
//   <template #header>
//     <TableHeader>Name</TableHeader>
//     <TableHeader>Value</TableHeader>
//   </template>
//   <TableRow>
//     <TableCell>Item 1</TableCell>
//     <TableCell>100</TableCell>
//   </TableRow>
// </Table>
</script>
